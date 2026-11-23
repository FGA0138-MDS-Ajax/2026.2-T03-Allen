import uuid
from datetime import datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func, text, true
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
    criado_em: Mapped[datetime] = mapped_column(
        "dhCriacao", DateTime(timezone=True), server_default=func.now()
    )

    # Preenchido temporariamente para resposta da API (não persistido)
    # WARNING: precisa persistir para notificacoes no wpp
    telefone: Mapped[str] = mapped_column("nuTelefone", String(255), unique=True)

    @property
    def tem_pin(self) -> bool:
        return self.hash_pin is not None


class Acompanhante(Base):
    """Relacionamento de convite entre o usuario e o acompanhante"""

    __tablename__ = "tblAcompanhamento"

    id_usuario_titular: Mapped[uuid.UUID] = mapped_column(
        "idUsuarioTitular", ForeignKey("tblUsuario.idUsuario"), primary_key=True
    )
    id_usuario_acompanhante: Mapped[uuid.UUID] = mapped_column(
        "idUsuarioAcompanhante", ForeignKey("tblUsuario.idUsuario"), primary_key=True
    )
    ic_pode_editar: Mapped[bool | None] = mapped_column("icPodeEditar")
    dh_aceite: Mapped[datetime | None] = mapped_column(
        "dhAceite", DateTime(timezone=True), nullable=True
    )
    dh_criacao: Mapped[datetime] = mapped_column(
        "dhCriacao", DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[str] = mapped_column("noStatus", default="pendente", nullable=False)
    dh_revogacao: Mapped[datetime | None] = mapped_column(
        "dhRevogacao", DateTime(timezone=True), nullable=True
    )
