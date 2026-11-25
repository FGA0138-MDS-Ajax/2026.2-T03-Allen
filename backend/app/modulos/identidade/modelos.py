import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func, text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.banco import Base


class Usuario(Base):
    """Usuário titular. Os nomes das colunas seguem o schema do banco (`tblUsuario`)."""

    __tablename__ = "tblUsuario"

    id: Mapped[uuid.UUID] = mapped_column(
        "idUsuario",
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    nome: Mapped[str] = mapped_column("noUsuario", String(255))
    hash_telefone: Mapped[str] = mapped_column("hashTelefone", String(255), unique=True)
    email: Mapped[str] = mapped_column("noEmail", String(255), unique=True)
    hash_pin: Mapped[str] = mapped_column("hashPin", Text)
    tentativas: Mapped[int] = mapped_column("nuTentativas", default=0)
    bloqueado_ate: Mapped[datetime | None] = mapped_column(
        "dhBloqueio", DateTime(timezone=True)
    )
    # Sobe quando o PIN muda: tokens com versão antiga deixam de valer
    versao_token: Mapped[int] = mapped_column(
        "nuVersaoToken", default=0, server_default=text("0")
    )
    dias_alerta: Mapped[int] = mapped_column("nuDiasAlerta", server_default=text("3"))
    audio_ativado: Mapped[bool] = mapped_column("icAudioAtivado", server_default=true())
    whatsapp_ativo: Mapped[bool] = mapped_column(
        "icWhatsAppAtivo", server_default=true()
    )
    # Resumo semanal e mensal no WhatsApp (RF24); desliga com "parar resumo"
    resumo_ativo: Mapped[bool] = mapped_column("icResumoAtivo", server_default=true())
    criado_em: Mapped[datetime] = mapped_column(
        "dhCriacao", DateTime(timezone=True), server_default=func.now()
    )

    # Número para o lembrete no WhatsApp (RF28). Opcional: quem se cadastrou antes da
    # migration dae0c2713ca6 só tem o hash, e o lembrete pula quem não tem número.
    telefone: Mapped[str | None] = mapped_column("nuTelefone", String(255), unique=True)

    @property
    def tem_pin(self) -> bool:
        return self.hash_pin is not None
