from enum import StrEnum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class AdaptadorEmail(StrEnum):
    """Valores do ENVIO_EMAIL."""

    FALSO = "falso"
    SMTP = "smtp"


class Settings(BaseSettings):
    APP_NAME: str = "Vero"

    DATABASE_URL: str
    SECRET_KEY: str
    JWT_ALGORITMO: str = "HS256"
    # Eventos em tempo real (D12). O padrão aponta para o serviço do docker-compose.
    VALKEY_URL: str = "redis://valkey:6379/0"
    # Envio de e-mail (código do "esqueci meu PIN"). Em desenvolvimento, o adaptador
    # falso só mostra o e-mail no log; com "smtp", usa o servidor das variáveis SMTP_*.
    ENVIO_EMAIL: AdaptadorEmail = AdaptadorEmail.FALSO
    SMTP_HOST: str = ""
    SMTP_PORTA: int = 587
    SMTP_USUARIO: str = ""
    SMTP_SENHA: str = ""
    SMTP_TLS: bool = True
    EMAIL_REMETENTE: str = "Vero <nao-responda@vero.app>"

    model_config = SettingsConfigDict(
        env_file=[
            BASE_DIR.parent.parent.parent / ".env",
            BASE_DIR.parent.parent / ".env",
            ".env",
        ],
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
