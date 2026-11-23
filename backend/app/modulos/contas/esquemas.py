"""Entrada e saída do módulo de contas (RF25)."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    StringConstraints,
    ValidationInfo,
    field_validator,
)

from app.modulos.contas.mensagens import Message
from app.modulos.contas.parcelas import CENTAVO, Parcelamento

# vrSaldo é decimal(12,2): no máximo 10 dígitos antes da vírgula
VALOR_MAXIMO = Decimal("9999999999.99")

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")


def hoje_brasilia() -> date:
    return datetime.now(FUSO_BRASILIA).date()


def vencimento_minimo(hoje: date) -> date:
    """Dia 1º do mês anterior (#121): a conta atrasada do mês passado ainda pode ser
    cadastrada; uma data de anos atrás é erro de toque no seletor."""
    if hoje.month == 1:
        return date(hoje.year - 1, 12, 1)
    return date(hoje.year, hoje.month - 1, 1)


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
    Na compra parcelada (RF37), `vencimento_em` é a data da compra e `valor` é o total:
    a 1ª parcela vence no mês seguinte.
    """

    vencimento_em: date
    valor: Valor
    descricao: Descricao | None = None
    categoria_id: int | None = None
    # RF26: repete todo mês; o lançamento automático no saldo é o RF18
    recorrente: bool = False
    # RF37: número de parcelas da compra; vazio quando não é parcelada
    parcelas: int | None = None

    @field_validator("vencimento_em")
    @classmethod
    def _validar_vencimento(cls, vencimento: date) -> date:
        minimo = vencimento_minimo(hoje_brasilia())
        if vencimento < minimo:
            raise ValueError(
                Message.VENCIMENTO_MUITO_ANTIGO.message.format(
                    data=minimo.strftime("%d/%m/%Y")
                )
            )
        return vencimento

    @field_validator("parcelas")
    @classmethod
    def _validar_parcelas(
        cls, parcelas: int | None, info: ValidationInfo
    ) -> int | None:
        if parcelas is None:
            return None
        minimo, maximo = Parcelamento.MINIMO.value, Parcelamento.MAXIMO.value
        if not minimo <= parcelas <= maximo:
            raise ValueError(
                Message.PARCELAS_FORA_DO_LIMITE.message.format(
                    minimo=minimo, maximo=maximo
                )
            )
        if info.data.get("recorrente"):
            raise ValueError(Message.PARCELADA_E_FIXA.message)
        valor = info.data.get("valor")
        if valor is not None and valor < parcelas * CENTAVO:
            raise ValueError(Message.VALOR_MENOR_QUE_PARCELAS.message)
        return parcelas


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
    recorrente: bool
    id_conta_origem: UUID | None = None
    # RF37: "parcela de total_parcelas" (ex.: 2 de 3); vazio quando não é parcela
    parcela: int | None = None
    total_parcelas: int | None = None


class ContaAutomaticaVencida(BaseModel):
    """O que o lançamento automático (RF18, RF37) precisa saber da conta fixa ou da
    parcela. O módulo de transações recebe estes dados pelo serviço de contas, sem ler
    a tblConta."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    usuario_id: UUID
    valor: Decimal
    vencimento_em: date
    descricao: str | None
    categoria_id: int | None
    parcela: int | None
    total_parcelas: int | None

class CategoriaSaida(BaseModel):
    id: int
    codigo: str
    nome: str
