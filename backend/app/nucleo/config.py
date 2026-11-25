import secrets
from enum import StrEnum
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Ambiente(StrEnum):
    """Valores do APP_ENV."""

    DESENVOLVIMENTO = "development"
    STAGING = "staging"
    PRODUCAO = "production"


class AdaptadorEmail(StrEnum):
    """Valores do ENVIO_EMAIL."""

    FALSO = "falso"
    SMTP = "smtp"


class AdaptadorWhatsApp(StrEnum):
    """Valores do ENVIO_WHATSAPP."""

    FALSO = "falso"
    API = "api"


class AdaptadorLeitorComprovante(StrEnum):
    """Valores do LEITOR_COMPROVANTE."""

    FALSO = "falso"
    CLAUDE = "claude"


class Settings(BaseSettings):
    APP_NAME: str = "Vero"
    # Sem APP_ENV, a API se comporta como produção: só aceita o e-mail de verdade
    APP_ENV: Ambiente = Ambiente.PRODUCAO

    # Autenticação e Banco
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
    # Chave do hash do código de recuperação do PIN, separada da SECRET_KEY (que assina
    # o token). Obrigatória fora do desenvolvimento.
    CHAVE_CODIGO_RECUPERACAO: str = ""
    # Chave de envio de WhatsApp (padrão: falso para dev)
    ENVIO_WHATSAPP: AdaptadorWhatsApp = AdaptadorWhatsApp.FALSO
    # APENAS EM PRODUCAO
    WHATSAPP_API_URL: str = ""
    WHATSAPP_TOKEN: str = ""

    # Leitura de fotos de comprovantes (RF14). O falso não lê nada: o assistente cai
    # no preenchimento manual (RF16). Com "claude", usa a API da Anthropic.
    LEITOR_COMPROVANTE: AdaptadorLeitorComprovante = AdaptadorLeitorComprovante.FALSO
    AI_API_KEY: str = ""
    AI_MODELO: str = "claude-opus-5-5"
    # RNF04 pede resposta em até 5 s; acima disto a leitura é abandonada e o
    # assistente pede os dados à pessoa
    AI_TIMEOUT_SEGUNDOS: float = 8.0

    # WhatsApp / Evolution API
    EVOLUTION_URL: str = ""
    AUTHENTICATION_API_KEY: str = ""
    INSTANCE_NAME: str = ""

    model_config = SettingsConfigDict(
        env_file=[
            BASE_DIR.parent.parent.parent / ".env",
            BASE_DIR.parent.parent / ".env",
            ".env",
        ],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _exigir_configuracao_fora_do_desenvolvimento(self) -> "Settings":
        if self.APP_ENV == Ambiente.DESENVOLVIMENTO:
            if not self.CHAVE_CODIGO_RECUPERACAO:
                # Só em desenvolvimento: uma chave nova a cada vez que a API sobe
                self.CHAVE_CODIGO_RECUPERACAO = secrets.token_hex(32)
            return self
        if self.ENVIO_EMAIL == AdaptadorEmail.FALSO:
            raise ValueError(
                "ENVIO_EMAIL=falso só é permitido com APP_ENV=development. "
                "Fora do desenvolvimento, use ENVIO_EMAIL=smtp."
            )
        if not self.CHAVE_CODIGO_RECUPERACAO:
            raise ValueError(
                "Defina CHAVE_CODIGO_RECUPERACAO (diferente da SECRET_KEY) "
                "fora do desenvolvimento."
            )
        if (
            self.LEITOR_COMPROVANTE == AdaptadorLeitorComprovante.CLAUDE
            and not self.AI_API_KEY
        ):
            raise ValueError("LEITOR_COMPROVANTE=claude exige AI_API_KEY.")
        return self


settings = Settings()
