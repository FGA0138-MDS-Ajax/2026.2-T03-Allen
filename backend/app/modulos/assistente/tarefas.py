"""Tarefas assíncronas do módulo Assistente executadas pelo worker do Celery (RF13, RNF04)."""

import asyncio
import logging
from typing import Any

from celery.signals import worker_process_init

from app.integracoes.transcricao import AdaptadorWhisper
from app.modulos.assistente.audio import processar_audio_mensagem
from app.nucleo.config import AdaptadorTranscricao, settings
from app.nucleo.tarefas import fila

logger = logging.getLogger(__name__)


@worker_process_init.connect
def _precarregar_modelo_whisper(**_: Any) -> None:
    """Mantém o modelo faster-whisper pré-carregado na memória do worker (M4)."""
    if settings.TRANSCRICAO_AUDIO == AdaptadorTranscricao.WHISPER:
        try:
            AdaptadorWhisper().precarregar()
        except Exception as erro:
            logger.warning(
                "Não foi possível pré-carregar o Whisper no worker: %s",
                type(erro).__name__,
            )


@fila.task(name="assistente.processar_audio")
def processar_audio_tarefa(remetente: str, data: dict[str, Any]) -> dict[str, Any]:
    """RF13: transcreve o áudio recebido no WhatsApp fora da requisição HTTP."""
    return asyncio.run(processar_audio_mensagem(remetente, data))
