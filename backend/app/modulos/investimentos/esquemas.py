"""Entrada e saída do módulo de investimentos (RF35).

Os dados seguem o que os bancos guardam de cada aplicação: produto, instituição, valor,
data da aplicação, vencimento, rentabilidade contratada e liquidez. O valor atual não é
guardado: é calculado a partir destes dados (RF36).
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum, StrEnum
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

from app.modulos.investimentos.mensagens import Message

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")


class Limites(Enum):
    """Limites dos valores do investimento."""

    # vrAplicado é decimal(12,2): no máximo 10 dígitos antes da vírgula
    VALOR_MAXIMO = Decimal("9999999999.99")
    # Prefixado: % ao ano
    TAXA_PREFIXADA_MAXIMA = Decimal("100")
    # Pós-fixado: % do CDI (ex.: 110% do CDI)
    PERCENTUAL_CDI_MAXIMO = Decimal("300")


class TipoInvestimento(StrEnum):
    """Valores do noTipoInvestimento (RF35: Renda Fixa ou CDB)."""

    CDB = "cdb"
    # Outras aplicações de renda fixa: LCI, LCA, Tesouro, poupança...
    RENDA_FIXA = "renda_fixa"


class Indexador(StrEnum):
    """Como a rentabilidade foi contratada (noIndexador)."""

    # Taxa fixa ao ano, conhecida no dia da aplicação (ex.: 12% ao ano)
    PREFIXADO = "prefixado"
    # Porcentagem do CDI (ex.: 110% do CDI)
    CDI = "cdi"


def hoje_brasilia() -> date:
    return datetime.now(FUSO_BRASILIA).date()


def _validar_nome(nome: str) -> str:
    if not nome:
        raise ValueError(Message.NOME_EM_BRANCO.message)
    return nome


def _validar_valor(valor: Decimal) -> Decimal:
    if valor <= 0:
        raise ValueError(Message.VALOR_INVALIDO.message)
    if valor > Limites.VALOR_MAXIMO.value:
        raise ValueError(Message.VALOR_MUITO_ALTO.message)
    return valor


Nome = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=255),
    AfterValidator(_validar_nome),
]
Instituicao = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]
Valor = Annotated[Decimal, AfterValidator(_validar_valor)]


class InvestimentoCadastroEntrada(BaseModel):
    """RF35: nova aplicação em CDB ou outra renda fixa."""

    tipo: TipoInvestimento
    nome: Nome
    instituicao: Instituicao | None = None
    valor_aplicado: Valor
    aplicado_em: date
    # Dia em que o dinheiro volta; vazio quando não tem prazo
    vence_em: date | None = None
    indexador: Indexador
    # % ao ano (prefixado) ou % do CDI (cdi)
    taxa: Decimal
    # Dá para tirar o dinheiro a qualquer dia, sem esperar o vencimento
    liquidez_diaria: bool = False

    @field_validator("aplicado_em")
    @classmethod
    def _aplicacao_nao_pode_ser_no_futuro(cls, aplicado_em: date) -> date:
        if aplicado_em > hoje_brasilia():
            raise ValueError(Message.APLICACAO_NO_FUTURO.message)
        return aplicado_em

    @field_validator("vence_em")
    @classmethod
    def _vencimento_depois_da_aplicacao(
        cls, vence_em: date | None, info: ValidationInfo
    ) -> date | None:
        aplicado_em = info.data.get("aplicado_em")
        if vence_em is not None and aplicado_em and vence_em <= aplicado_em:
            raise ValueError(Message.VENCIMENTO_ANTES_DA_APLICACAO.message)
        return vence_em

    @field_validator("taxa")
    @classmethod
    def _taxa_dentro_do_limite(cls, taxa: Decimal, info: ValidationInfo) -> Decimal:
        indexador = info.data.get("indexador")
        if indexador is None:
            # O indexador já deu erro; o limite da taxa depende dele
            return taxa
        if indexador == Indexador.CDI:
            maximo, mensagem = (
                Limites.PERCENTUAL_CDI_MAXIMO.value,
                Message.PERCENTUAL_CDI_FORA_DO_LIMITE,
            )
        else:
            maximo, mensagem = (
                Limites.TAXA_PREFIXADA_MAXIMA.value,
                Message.TAXA_PREFIXADA_FORA_DO_LIMITE,
            )
        if not Decimal("0") < taxa <= maximo:
            raise ValueError(mensagem.message.format(maximo=maximo))
        return taxa


class InvestimentoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tipo: TipoInvestimento
    nome: str
    instituicao: str | None
    valor_aplicado: Decimal
    aplicado_em: date
    vence_em: date | None
    indexador: Indexador
    taxa: Decimal
    liquidez_diaria: bool
    criado_em: datetime
