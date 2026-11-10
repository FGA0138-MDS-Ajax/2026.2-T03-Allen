"""Portas: interfaces para os serviços externos (Portas e Adaptadores, D6).

Os módulos dependem só destas interfaces. Os adaptadores que as implementam ficam
em app/integracoes, e em desenvolvimento usam versões falsas (Quadro 7 do documento).
"""

from typing import Protocol


class PortaEmail(Protocol):
    def enviar(self, destinatario: str, assunto: str, texto: str) -> None:
        """Envia um e-mail de texto simples. Não lança erro: falhas ficam no log."""
