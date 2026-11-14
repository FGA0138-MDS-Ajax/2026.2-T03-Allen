"""Canal em tempo real com o app (RF17): WebSocket /ws.

1. O app abre o /ws e envia {"token": "<access_token>"} como primeira mensagem.
2. A API responde {"tipo": "conectado"}.
3. A cada evento do usuário (ex.: gasto registrado pelo WhatsApp), a API envia
   {"tipo": "transacao_criada", "dados": {...}}. O app então recarrega saldo,
   indicador de situação e histórico.

O token vai na mensagem, e não na URL, para não aparecer nos logs do servidor.
"""

import asyncio
import logging
import time
import uuid
from enum import Enum

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.modulos.identidade.mensagens import Message as MessageIdentidade
from app.modulos.identidade.seguranca import ler_token
from app.modulos.tempo_real.mensagens import Message
from app.nucleo import eventos

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tempo real"])


class Limites(Enum):
    """Prazos do canal em tempo real."""

    SEGUNDOS_PARA_ENVIAR_TOKEN = 10


class SessaoInvalida(Exception):
    pass


@router.websocket("/ws")
async def canal(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        usuario_id, expira_em = await _autenticar(websocket)
    # ValueError: a primeira mensagem não é um JSON
    except (SessaoInvalida, TimeoutError, ValueError):
        await websocket.close(
            status.WS_1008_POLICY_VIOLATION,
            MessageIdentidade.SESSAO_INVALIDA.message,
        )
        return
    except WebSocketDisconnect:
        return

    await websocket.send_json({"tipo": eventos.TipoEvento.CONECTADO})

    tarefas = {
        "eventos": asyncio.create_task(_repassar_eventos(websocket, usuario_id)),
        "desconexao": asyncio.create_task(_esperar_desconexao(websocket)),
        "expiracao": asyncio.create_task(asyncio.sleep(expira_em - time.time())),
    }
    concluidas, pendentes = await asyncio.wait(
        tarefas.values(), return_when=asyncio.FIRST_COMPLETED
    )
    for tarefa in pendentes:
        tarefa.cancel()
    resultados = await asyncio.gather(*tarefas.values(), return_exceptions=True)

    if tarefas["desconexao"] in concluidas:
        return
    if tarefas["expiracao"] in concluidas:
        codigo = status.WS_1008_POLICY_VIOLATION
        motivo = MessageIdentidade.SESSAO_INVALIDA.message
    else:
        # O repasse de eventos parou: o Valkey caiu ou o envio ao app falhou
        erro = resultados[0]
        logger.warning("Canal em tempo real interrompido: %s", type(erro).__name__)
        codigo = status.WS_1011_INTERNAL_ERROR
        motivo = Message.TEMPO_REAL_INDISPONIVEL.message
    try:
        await websocket.close(codigo, motivo)
    except RuntimeError:
        pass  # o app já tinha fechado a conexão


async def _autenticar(websocket: WebSocket) -> tuple[uuid.UUID, float]:
    """Lê o token da primeira mensagem. Devolve o id do usuário e quando o token vence."""
    primeira = await asyncio.wait_for(
        websocket.receive_json(), Limites.SEGUNDOS_PARA_ENVIAR_TOKEN.value
    )
    if not isinstance(primeira, dict) or not isinstance(primeira.get("token"), str):
        raise SessaoInvalida
    try:
        dados = ler_token(primeira["token"])
        return uuid.UUID(dados["sub"]), float(dados["exp"])
    except (jwt.PyJWTError, ValueError):
        raise SessaoInvalida from None


async def _repassar_eventos(websocket: WebSocket, usuario_id: uuid.UUID) -> None:
    async for mensagem in eventos.ouvir(usuario_id):
        await websocket.send_text(mensagem)


async def _esperar_desconexao(websocket: WebSocket) -> None:
    """O app não precisa mandar nada depois do token; mensagens extras são ignoradas."""
    while True:
        mensagem = await websocket.receive()
        if mensagem["type"] == "websocket.disconnect":
            return
