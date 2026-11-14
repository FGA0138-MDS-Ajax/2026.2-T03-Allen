"""Gasto ou receita do usuário. Colunas seguem o schema do banco (`tblTransacao`)."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.banco import Base


class Transacao(Base):
    __tablename__ = "tblTransacao"

    id: Mapped[uuid.UUID] = mapped_column(
        "idTransacao", primary_key=True, server_default=text("gen_random_uuid()")
    )
    # FK existe no banco. Não declarada aqui para o registro funcionar mesmo em um
    # processo que não carregou o model de Usuario (ex.: worker ou script)
    usuario_id: Mapped[uuid.UUID] = mapped_column("idUsuario")
    # Texto com CHECK no banco; aqui validados por TipoTransacao e OrigemTransacao
    tipo: Mapped[str] = mapped_column("noTipoTransacao", String)
    valor: Mapped[Decimal] = mapped_column("vrTransacao", Numeric(12, 2))
    data: Mapped[date] = mapped_column("dtTransacao", Date)
    descricao: Mapped[str | None] = mapped_column("descTransacao", Text)
    # FK existe no banco; sem model de Categoria ainda, não declaramos aqui
    categoria_id: Mapped[int | None] = mapped_column("idCategoria", BigInteger)
    origem: Mapped[str] = mapped_column("noOrigem", String)
    chave_externa: Mapped[str | None] = mapped_column("coChaveExterna", Text)

    criado_em: Mapped[datetime] = mapped_column(
        "dhCriacao", DateTime(timezone=True), server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        "dhAtualizacao", DateTime(timezone=True), server_default=func.now()
    )
