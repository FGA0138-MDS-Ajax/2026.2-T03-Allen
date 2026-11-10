import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func, text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.banco import Base


class Usuario(Base):
    """Usuário titular. Os nomes das colunas seguem o schema do banco (`tblUsuario`)."""

    __tablename__ = "tblUsuario"

    id: Mapped[uuid.UUID] = mapped_column(
        "idUsuario", primary_key=True, server_default=text("gen_random_uuid()")
    )
    nome: Mapped[str] = mapped_column("noUsuario", String(255))
    telefone: Mapped[str] = mapped_column("nuTelefone", String(255), unique=True)
    email: Mapped[str] = mapped_column("noEmail", String(255), unique=True)
    # hashUsuario guarda o hash da senha; o PIN, opcional, fica em hashPin
    hash_senha: Mapped[str] = mapped_column("hashUsuario", Text)
    hash_pin: Mapped[str | None] = mapped_column("hashPin", Text)
    tentativas: Mapped[int] = mapped_column("nuTentativas", default=0)
    bloqueado_ate: Mapped[datetime | None] = mapped_column(
        "dhBloqueio", DateTime(timezone=True)
    )
    dias_alerta: Mapped[int] = mapped_column("nuDiasAlerta", server_default=text("3"))
    audio_ativado: Mapped[bool] = mapped_column("icAudioAtivado", server_default=true())
    whatsapp_ativo: Mapped[bool] = mapped_column(
        "icWhatsAppAtivo", server_default=true()
    )
    criado_em: Mapped[datetime] = mapped_column(
        "dhCriacao", DateTime(timezone=True), server_default=func.now()
    )

    @property
    def tem_pin(self) -> bool:
        return self.hash_pin is not None
