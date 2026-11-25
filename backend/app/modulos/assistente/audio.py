"""Processamento de mensagens de áudio do assistente no WhatsApp (RF13 / RNF04 / LGPD)."""

import base64
import logging
import time
from typing import Any

import httpx

from app.integracoes.transcricao import obter_transcricao
from app.modulos.assistente import mensagens
from app.modulos.transacoes.esquemas import OrigemTransacao
from app.nucleo.config import settings
from app.nucleo.portas import AudioMuitoLongo, FalhaTranscricao, PortaTranscricao

logger = logging.getLogger(__name__)


def _urls_evolution(caminho: str) -> list[str]:
    urls = [f"{settings.EVOLUTION_URL}{caminho}"]
    if "localhost" in settings.EVOLUTION_URL:
        urls.append(
            f"{settings.EVOLUTION_URL.replace('localhost', 'evolution-api')}{caminho}"
        )
    elif "evolution-api" in settings.EVOLUTION_URL:
        urls.append(
            f"{settings.EVOLUTION_URL.replace('evolution-api', 'localhost')}{caminho}"
        )
    return urls


async def baixar_audio_evolution(data: dict[str, Any]) -> tuple[bytes, str]:
    """Obtém os bytes do áudio recebido pela Evolution API (base64 direto ou via REST)."""
    message = data.get("message", {})
    audio_msg = message.get("audioMessage", {}) or {}
    mime_type = audio_msg.get("mimetype", "audio/ogg")

    b64 = message.get("base64") or data.get("base64")
    if isinstance(b64, str) and b64.strip():
        return base64.b64decode(b64), mime_type

    headers = {
        "apikey": settings.AUTHENTICATION_API_KEY,
        "Content-Type": "application/json",
    }
    body = {"message": {"key": data.get("key", {})}}
    caminho = f"/chat/getBase64FromMediaMessage/{settings.INSTANCE_NAME}"

    async with httpx.AsyncClient() as client:
        for url in _urls_evolution(caminho):
            try:
                resposta = await client.post(
                    url, json=body, headers=headers, timeout=5.0
                )
                resposta.raise_for_status()
                conteudo = resposta.json()
                b64_remoto = conteudo.get("base64")
                if isinstance(b64_remoto, str) and b64_remoto.strip():
                    return base64.b64decode(b64_remoto), mime_type
            except Exception as erro:
                logger.warning(
                    "Falha ao baixar mídia da Evolution API em %s: %s",
                    url,
                    type(erro).__name__,
                )

    raise FalhaTranscricao("Não foi possível baixar o áudio da Evolution API.")


async def processar_audio_mensagem(
    remetente: str,
    data: dict[str, Any],
    adaptador_transcricao: PortaTranscricao | None = None,
) -> dict[str, Any]:
    """Baixa, transcreve e encaminha o áudio para o mesmo parser do RF12.

    Descarta os bytes do áudio imediatamente após a transcrição (LGPD).
    """
    import app.modulos.assistente.router as assistente_router

    inicio = time.perf_counter()
    telefone = remetente.split("@")[0] if "@" in remetente else remetente

    usuario = assistente_router.buscar_usuario_telefone(telefone)
    if not usuario:
        await assistente_router.enviar_mensagem(
            remetente, mensagens.usuario_nao_encontrado()
        )
        return {"status": "usuario_nao_encontrado"}

    audio_msg = data.get("message", {}).get("audioMessage", {}) or {}
    duracao_audio = audio_msg.get("seconds")
    if (
        isinstance(duracao_audio, (int, float))
        and duracao_audio > settings.AUDIO_MAX_DURACAO_SEGUNDOS
    ):
        await assistente_router.enviar_mensagem(
            remetente, mensagens.audio_muito_longo()
        )
        return {"status": "audio_muito_longo"}

    audio_bytes: bytes | None = None
    try:
        audio_bytes, mime_type = await baixar_audio_evolution(data)
        adaptador = adaptador_transcricao or obter_transcricao()
        texto_transcrito = adaptador.transcrever(audio_bytes, mime_type=mime_type)
    except AudioMuitoLongo:
        await assistente_router.enviar_mensagem(
            remetente, mensagens.audio_muito_longo()
        )
        return {"status": "audio_muito_longo"}
    except FalhaTranscricao:
        await assistente_router.enviar_mensagem(
            remetente, mensagens.audio_nao_compreendido()
        )
        return {"status": "falha_transcricao"}
    finally:
        # Garante descarte imediato do áudio em memória após o processamento (LGPD)
        if audio_bytes is not None:
            del audio_bytes

    await assistente_router.processar_responder(
        remetente,
        texto_transcrito,
        origem=OrigemTransacao.WHATSAPP_AUDIO,
    )

    duracao_ms = (time.perf_counter() - inicio) * 1000
    # Log sem telefone, transcrição ou valor (RNF05)
    logger.info("Processamento de áudio concluído em %.0f ms.", duracao_ms)
    return {"status": "ok", "duracao_ms": round(duracao_ms, 2)}
