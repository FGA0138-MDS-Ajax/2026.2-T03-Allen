"""Entrada e saída do módulo de contas (RF25)."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints

from app.modulos.contas.mensagens import Message

# vrSaldo é decimal(12,2): no máximo 10 dígitos antes da vírgula
VALOR_MAXIMO = Decimal("9999999999.99")


class StatusConta(StrEnum):
    """Situação da conta, calculada a partir do pagamento e do vencimento."""

    A_VENCER = "a_vencer"
    PAGA = "paga"
    EM_ATRASO = "em_atraso"


def validar_valor(valor: Decimal) -> Decimal:
    if valor <= 0:
        raise ValueError(Message.VALOR_INVALIDO.message)
    if valor > VALOR_MAXIMO:
        raise ValueError(Message.VALOR_MUITO_ALTO.message)
    return valor


Valor = Annotated[Decimal, AfterValidator(validar_valor)]
Descricao = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]


class ContaCadastroEntrada(BaseModel):
    """RF25: apenas data e valor são obrigatórios.

    Descrição e categoria são opcionais (card [S2] RF25: "nome ou ícone opcional").
    """

    vencimento_em: date
    valor: Valor
    descricao: Descricao | None = None
    categoria_id: int | None = None


class ContaPagamentoEntrada(BaseModel):
    """RF30: marca ou desfaz o pagamento de uma conta.

    Um único campo booleano mantém idempotente e permite o mesmo
    endpoint atender ao botão "Paga" e ao botão "Desfazer".
    """

    paga: bool


class ContaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    descricao: str | None
    valor: Decimal
    vencimento_em: date
    categoria_id: int | None
    status: StatusConta
    pagamento_em: datetime | None
    criado_em: datetime
