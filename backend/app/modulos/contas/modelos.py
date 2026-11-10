"""Conta a pagar do usuário. Colunas seguem o schema do banco (`tblConta`)."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Numeric, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.modulos.contas.esquemas import StatusConta
from app.nucleo.banco import Base

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")


class Conta(Base):
    __tablename__ = "tblConta"

    id: Mapped[uuid.UUID] = mapped_column(
        "idConta", primary_key=True, server_default=text("gen_random_uuid()")
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        "idUsuario", ForeignKey("tblUsuario.idUsuario")
    )
    valor: Mapped[Decimal] = mapped_column("vrSaldo", Numeric(12, 2))
    vencimento_em: Mapped[date] = mapped_column("dtProximoVencimento", Date)

    # Opcionais pelo RF25 / card [S2]
    descricao: Mapped[str | None] = mapped_column("descConta", Text)
    # FK existe no banco; sem model de Categoria ainda, não declaramos aqui
    categoria_id: Mapped[int | None] = mapped_column("idCategoria", BigInteger)

    # Preenchido quando a conta é marcada como paga (RF30, fora do RF25)
    pagamento_em: Mapped[datetime | None] = mapped_column(
        "dhPagamento", DateTime(timezone=True)
    )

    criado_em: Mapped[datetime] = mapped_column(
        "dhCriacao", DateTime(timezone=True), server_default=func.now()
    )

    @property
    def status(self) -> StatusConta:
        """Calculado no fuso de Brasília, conforme o Documento de Arquitetura."""
        if self.pagamento_em is not None:
            return StatusConta.PAGA
        if self.vencimento_em < datetime.now(FUSO_BRASILIA).date():
            return StatusConta.EM_ATRASO
        return StatusConta.A_VENCER

    def __str__(self) -> str:
        return f"{self.descricao or 'Conta'} — {self.valor}"
