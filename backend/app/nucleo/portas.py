"""Portas: interfaces para os serviços externos (Portas e Adaptadores, D6).

Os módulos dependem só destas interfaces. Os adaptadores que as implementam ficam
em app/integracoes, e em desenvolvimento usam versões falsas (Quadro 7 do documento).
"""

from typing import Protocol


class FalhaEnvioEmail(Exception):
    """O e-mail não foi enviado (ex.: servidor SMTP fora do ar)."""


class PortaEmail(Protocol):
    def enviar(self, destinatario: str, assunto: str, texto: str) -> None:
        """Envia um e-mail de texto simples. Lança FalhaEnvioEmail se não conseguir."""


class FalhaTranscricao(Exception):
    """Não foi possível transcrever o áudio (formato inválido ou erro no motor)."""


class AudioMuitoLongo(Exception):
    """Áudio excede a duração máxima permitida (60 s, RNF04)."""


class PortaTranscricao(Protocol):
    def transcrever(self, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
        """Transcreve o áudio em memória para texto em português.

        O chamador e a implementação devem descartar os bytes após o uso (LGPD).
        Lança FalhaTranscricao ou AudioMuitoLongo em caso de erro.
        """
