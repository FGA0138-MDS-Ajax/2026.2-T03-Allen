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


class FalhaEnvioWhatsApp(Exception):
    """A mensagem de WhatsApp não foi enviada."""


class PortaWhatsApp(Protocol):
    def enviar(self, destinatario: str, assunto: str, texto: str) -> None:
        """Envia uma mensagem de texto simples pelo WhatsApp. Lança FalhaEnvioWhatsApp se não conseguir."""
