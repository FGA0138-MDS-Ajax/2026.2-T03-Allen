"""Barramento de eventos pelo Valkey (D12).

Cada usuário tem um canal próprio. O módulo que muda algo de interesse do app
publica no canal; o WebSocket /ws repassa ao app do usuário (RF17).
"""

import json
import logging
import uuid
from collections.abc import AsyncIterator
from enum import StrEnum

import valkey
import valkey.asyncio as valkey_async

from app.nucleo.config import settings

logger = logging.getLogger(__name__)

cliente = valkey.Valkey.from_url(settings.VALKEY_URL)


class TipoEvento(StrEnum):
    """Valor do campo `tipo` das mensagens que o app recebe pelo /ws."""

    CONECTADO = "conectado"
    TRANSACAO_CRIADA = "transacao_criada"


def canal_do_usuario(usuario_id: uuid.UUID) -> str:
    return f"vero:usuario:{usuario_id}"


def publicar(usuario_id: uuid.UUID, tipo: TipoEvento, dados: dict) -> None:
    """Avisa o app do usuário. Se o Valkey falhar, o que já foi salvo continua salvo:
    o app vê a mudança na próxima vez que carregar os dados."""
    mensagem = json.dumps({"tipo": tipo, "dados": dados})
    try:
        cliente.publish(canal_do_usuario(usuario_id), mensagem)
    except valkey.ValkeyError:
        # Sem telefone nem valores no log (RNF05)
        logger.warning("Não foi possível publicar o evento %s no Valkey.", tipo)


async def ouvir(usuario_id: uuid.UUID) -> AsyncIterator[str]:
    """Entrega, em texto JSON, cada evento publicado no canal do usuário."""
    conexao = valkey_async.Valkey.from_url(
        settings.VALKEY_URL, decode_responses=True, socket_timeout=None
    )
    assinatura = conexao.pubsub(ignore_subscribe_messages=True)
    await assinatura.subscribe(canal_do_usuario(usuario_id))
    try:
        async for mensagem in assinatura.listen():
            yield mensagem["data"]
    finally:
        await assinatura.aclose()
        await conexao.aclose()
