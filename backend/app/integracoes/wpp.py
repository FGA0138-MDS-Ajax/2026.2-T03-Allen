import logging

from app.nucleo.config import AdaptadorWhatsApp, settings
from app.nucleo.portas import PortaWhatsApp

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
    def enviar(self, destinatario: str, assunto: str, texto: str) -> None:
        # TODO: integrar com api da whatsapp business
        # exemplo aqui:
        # import requests
        # mensagem = {"to": destinatario, "body": texto}
        # response = requests.post(
        #     settings.WHATSAPP_API_URL,
        #     json=mensagem,
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"})
        # response.raise_for_status()
        pass


def obter_whatsapp() -> PortaWhatsApp:
    """entrega o adaptador escolhido no ENVIO_WHATSAPP."""
    if settings.ENVIO_WHATSAPP == AdaptadorWhatsApp.API:
        return WppApi()
    return WhatsAppFalso()
