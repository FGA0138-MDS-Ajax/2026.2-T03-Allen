"""Aplicação do usuário em CDB ou outra renda fixa (RF35). Tabela `tblInvestimento`."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    false,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.banco import Base


class Investimento(Base):
    __tablename__ = "tblInvestimento"
    __table_args__ = (Index("tblinvestimento_idusuario_index", "idUsuario"),)

    id: Mapped[uuid.UUID] = mapped_column(
        "idInvestimento",
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        "idUsuario", ForeignKey("tblUsuario.idUsuario")
    )
    # Texto com CHECK no banco; aqui validados por TipoInvestimento e Indexador
    tipo: Mapped[str] = mapped_column("noTipoInvestimento", String(255))
    nome: Mapped[str] = mapped_column("noInvestimento", String(255))
    instituicao: Mapped[str | None] = mapped_column("noInstituicao", String(255))
    valor_aplicado: Mapped[Decimal] = mapped_column("vrAplicado", Numeric(12, 2))
    aplicado_em: Mapped[date] = mapped_column("dtAplicacao", Date)
    vence_em: Mapped[date | None] = mapped_column("dtVencimento", Date)
    indexador: Mapped[str] = mapped_column("noIndexador", String(255))
    taxa: Mapped[Decimal] = mapped_column("vrTaxa", Numeric(7, 2))
    liquidez_diaria: Mapped[bool] = mapped_column(
        "icLiquidezDiaria", default=False, server_default=false()
    )
    criado_em: Mapped[datetime] = mapped_column(
        "dhCriacao", DateTime(timezone=True), server_default=func.now()
    )
