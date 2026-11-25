"""Adaptadores da porta de transcrição de áudio (PortaTranscricao, RF13).

O TRANSCRICAO_AUDIO escolhe qual deles é usado:
- whisper (padrão): usa faster-whisper quantizado (int8) pré-carregado em memória
  para atender o limite de <= 5 s (RNF04).
- falso (só aceito com APP_ENV=development): retorna uma frase fixa para testes
  locais sem carregar o modelo de IA.
"""

import io
import logging
import threading
import time
from typing import Any

from app.nucleo.config import AdaptadorTranscricao, settings
from app.nucleo.portas import AudioMuitoLongo, FalhaTranscricao, PortaTranscricao

logger = logging.getLogger(__name__)

_PROMPT_INICIAL_PT = (
    "Gastei 35 reais na farmácia. Comprei pão no mercado. "
    "Paguei 120 de luz. Recebi 1500 da aposentadoria."
)


class AdaptadorWhisper:
    """Adaptador faster-whisper com modelo mantido em memória (int8) e descarte imediato do áudio."""

    _trava = threading.Lock()
    _modelos: dict[tuple[str, str], Any] = {}

    def __init__(
        self,
        modelo: str | None = None,
        compute_type: str | None = None,
        idioma: str | None = None,
        max_duracao_segundos: int | None = None,
    ) -> None:
        self._modelo_nome = modelo or settings.WHISPER_MODELO
        self._compute_type = compute_type or settings.WHISPER_COMPUTE_TYPE
        self._idioma = idioma or settings.WHISPER_IDIOMA
        self._max_duracao = max_duracao_segundos or settings.AUDIO_MAX_DURACAO_SEGUNDOS

    def _obter_modelo(self) -> Any:
        chave = (self._modelo_nome, self._compute_type)
        if chave in self._modelos:
            return self._modelos[chave]

        with self._trava:
            if chave not in self._modelos:
                try:
                    from faster_whisper import WhisperModel
                except ImportError as erro:
                    raise FalhaTranscricao(
                        "Dependência faster-whisper não instalada."
                    ) from erro

                inicio = time.perf_counter()
                self._modelos[chave] = WhisperModel(
                    self._modelo_nome,
                    device="cpu",
                    compute_type=self._compute_type,
                )
                carregamento_ms = (time.perf_counter() - inicio) * 1000
                logger.info(
                    "Modelo Whisper '%s' (%s) carregado em %.0f ms.",
                    self._modelo_nome,
                    self._compute_type,
                    carregamento_ms,
                )
        return self._modelos[chave]

    def precarregar(self) -> None:
        """Carrega o modelo na inicialização do worker para evitar latência na primeira requisição."""
        self._obter_modelo()

    def transcrever(self, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
        if not audio_bytes:
            raise FalhaTranscricao("Áudio vazio.")

        modelo = self._obter_modelo()
        buffer = io.BytesIO(audio_bytes)
        inicio = time.perf_counter()

        try:
            segmentos, info = modelo.transcribe(
                buffer,
                language=self._idioma,
                beam_size=2,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500},
                initial_prompt=_PROMPT_INICIAL_PT,
            )

            duracao = getattr(info, "duration", 0.0) or 0.0
            if duracao > self._max_duracao:
                raise AudioMuitoLongo(
                    f"Áudio excede o limite de {self._max_duracao} s."
                )

            texto = " ".join(
                seg.text.strip()
                for seg in segmentos
                if getattr(seg, "text", "").strip()
            ).strip()
        except AudioMuitoLongo:
            raise
        except Exception as erro:
            logger.exception("Falha na transcrição de áudio: %s", type(erro).__name__)
            raise FalhaTranscricao("Não foi possível transcrever o áudio.") from erro
        finally:
            # Descarta imediatamente o buffer de áudio da memória (LGPD)
            buffer.close()
            del buffer

        duracao_ms = (time.perf_counter() - inicio) * 1000
        # Não registra texto transcrito, telefone ou valores no log (RNF05)
        logger.info("Áudio transcrito em %.0f ms.", duracao_ms)

        if not texto:
            raise FalhaTranscricao("Transcrição vazia.")

        return texto


class TranscricaoFalsa:
    """Adaptador falso para desenvolvimento e testes sem modelo Whisper carregado."""

    def __init__(self, texto_padrao: str = "gastei 35 na farmácia") -> None:
        self._texto_padrao = texto_padrao

    def transcrever(self, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
        if not audio_bytes:
            raise FalhaTranscricao("Áudio vazio.")
        logger.warning(
            "Transcrição NÃO executada no Whisper (adaptador falso de desenvolvimento)."
        )
        return self._texto_padrao


def obter_transcricao() -> PortaTranscricao:
    """Entrega o adaptador configurado em TRANSCRICAO_AUDIO."""
    if settings.TRANSCRICAO_AUDIO == AdaptadorTranscricao.FALSO:
        return TranscricaoFalsa()
    return AdaptadorWhisper()
