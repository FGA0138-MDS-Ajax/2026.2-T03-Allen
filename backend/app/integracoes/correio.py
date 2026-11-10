"""Adaptadores da porta de e-mail (PortaEmail).

O ENVIO_EMAIL escolhe qual deles a API usa:
- falso (padrão, desenvolvimento): não envia; mostra o e-mail no log do backend
  (docker compose logs backend).
- smtp: envia pelo servidor configurado nas variáveis SMTP_*.
"""

import logging
import smtplib
from email.message import EmailMessage

from app.nucleo.config import AdaptadorEmail, settings
from app.nucleo.portas import PortaEmail

logger = logging.getLogger(__name__)


class EmailSmtp:
    def enviar(self, destinatario: str, assunto: str, texto: str) -> None:
        mensagem = EmailMessage()
        mensagem["From"] = settings.EMAIL_REMETENTE
        mensagem["To"] = destinatario
        mensagem["Subject"] = assunto
        mensagem.set_content(texto)
        try:
            with smtplib.SMTP(
                settings.SMTP_HOST, settings.SMTP_PORTA, timeout=10
            ) as smtp:
                if settings.SMTP_TLS:
                    smtp.starttls()
                if settings.SMTP_USUARIO:
                    smtp.login(settings.SMTP_USUARIO, settings.SMTP_SENHA)
                smtp.send_message(mensagem)
        except (OSError, smtplib.SMTPException) as erro:
            # Sem o endereço no log (RNF05)
            logger.warning("Não foi possível enviar o e-mail: %s", type(erro).__name__)


class EmailFalso:
    """Só para desenvolvimento, com dados fictícios: o e-mail aparece no log."""

    def enviar(self, destinatario: str, assunto: str, texto: str) -> None:
        logger.warning(
            "E-mail NÃO enviado (adaptador falso de desenvolvimento).\nAssunto: %s\n%s",
            assunto,
            texto,
        )


def obter_email() -> PortaEmail:
    """Dependência do FastAPI: entrega o adaptador escolhido no ENVIO_EMAIL."""
    if settings.ENVIO_EMAIL == AdaptadorEmail.SMTP:
        return EmailSmtp()
    return EmailFalso()
