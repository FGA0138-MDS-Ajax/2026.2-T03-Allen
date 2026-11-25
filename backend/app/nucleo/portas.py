"""Portas: interfaces para os serviços externos (Portas e Adaptadores, D6).

Os módulos dependem só destas interfaces. Os adaptadores que as implementam ficam
em app/integracoes, e em desenvolvimento usam versões falsas (Quadro 7 do documento).
"""

from dataclasses import dataclass
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


class FalhaEnvioWhatsApp(Exception):
    """A mensagem de WhatsApp não foi enviada."""


class PortaWhatsApp(Protocol):
    def enviar(self, destinatario: str, assunto: str, texto: str) -> None:
        """Envia uma mensagem de texto simples pelo WhatsApp. Lança FalhaEnvioWhatsApp se não conseguir."""


class FalhaLeituraComprovante(Exception):
    """A foto não pôde ser lida (serviço fora do ar, demorou demais, etc.)."""


class PortaLeitorComprovante(Protocol):
    async def ler(
        self, imagem: bytes, tipo_mime: str, legenda: str | None
    ) -> "LeituraComprovante":
        """Lê valor, tipo e categoria da foto de um comprovante, nota fiscal ou conta
        (RF14). Lança FalhaLeituraComprovante se não conseguir ler."""


@dataclass
class LeituraComprovante:
    """O que foi lido da foto. Campo vazio = não identificado (o assistente pede)."""

    # Em centavos
    valor: int | None = None
    # "GASTO", "RECEITA" ou vazio
    tipo: str = ""
    categoria: str = ""
    descricao: str = ""
