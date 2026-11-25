import logging

import httpx

from app.nucleo.config import AdaptadorWhatsApp, settings
from app.nucleo.portas import FalhaEnvioWhatsApp, PortaWhatsApp

logger = logging.getLogger(__name__)


class WhatsAppFalso:
    """uso destinado apenas para dev, tem dados ficticios aqui"""

    def enviar(self, destinatario: str, assunto: str, texto: str) -> None:
        logger.warning(
            "whatsapp não enviado (adaptador falso apenas para dev)/\nAssunto: %s\n%s",
            assunto,
            texto,
        )


class WppApi:
    """Envia pela Evolution API, o mesmo canal em que o assistente responde
    (#152). Usado pelas mensagens que o Vero manda sozinho: lembrete (RF28) e
    resumo (RF24)."""

    def enviar(self, destinatario: str, assunto: str, texto: str) -> None:
        numero = destinatario.split("@")[0]
        url = f"{settings.EVOLUTION_URL}/message/sendText/{settings.INSTANCE_NAME}"
        try:
            resposta = httpx.post(
                url,
                json={"number": numero, "text": texto},
                headers={"apikey": settings.AUTHENTICATION_API_KEY},
                timeout=10.0,
            )
            resposta.raise_for_status()
        except httpx.HTTPError as erro:
            # Sem número nem texto no log (RNF05): quem chama registra a falha
            raise FalhaEnvioWhatsApp(
                f"Evolution API não aceitou a mensagem ({erro.__class__.__name__})"
            ) from erro


def obter_whatsapp() -> PortaWhatsApp:
    """entrega o adaptador escolhido no ENVIO_WHATSAPP."""
    if settings.ENVIO_WHATSAPP == AdaptadorWhatsApp.API:
        return WppApi()
    return WhatsAppFalso()
