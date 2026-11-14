"""Entrada e saída do módulo de transações (RF10, RF17)."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    StringConstraints,
    model_validator,
)

from app.modulos.transacoes.mensagens import Message

# vrTransacao é decimal(12,2): no máximo 10 dígitos antes da vírgula
VALOR_MAXIMO = Decimal("9999999999.99")


class TipoTransacao(StrEnum):
    """Valores do enum noTipoTransacao do banco."""

    ENTRADA = "entrada"
    SAIDA = "saida"


class OrigemTransacao(StrEnum):
    """Valores do enum noOrigem da tblTransacao."""

    MANUAL = "manual"
    WHATSAPP_TEXTO = "whatsapp_texto"
    WHATSAPP_AUDIO = "whatsapp_audio"
    WHATSAPP_FOTO = "whatsapp_foto"
    QRCODE_NF = "qrcode_nf"
    EXTRATO = "extrato"
    CONTA = "conta"


def validar_valor(valor: Decimal) -> Decimal:
    if valor <= 0:
        raise ValueError(Message.VALOR_INVALIDO.message)
    if valor > VALOR_MAXIMO:
        raise ValueError(Message.VALOR_MUITO_ALTO.message)
    return valor


Valor = Annotated[Decimal, AfterValidator(validar_valor)]
Descricao = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]


class TransacaoRegistroEntrada(BaseModel):
    """Gasto ou receita a registrar. Usado pelo assistente do WhatsApp depois que
    o usuário confirma (RF15) e, no futuro, pelo registro manual no app."""

    tipo: TipoTransacao
    valor: Valor
    origem: OrigemTransacao
    # Vazio: hoje, no fuso de Brasília
    data: date | None = None
    descricao: Descricao | None = None
    categoria_id: int | None = None
    # Identificador de quem originou o registro (ex.: id da mensagem no WhatsApp).
    # Evita gravar duas vezes a mesma mensagem.
    chave_externa: str | None = None


class TransacaoEdicaoEntrada(BaseModel):
    """RF10: muda só os campos enviados. Descrição e categoria aceitam null para apagar;
    valor e data, não."""

    valor: Valor | None = None
    data: date | None = None
    descricao: Descricao | None = None
    categoria_id: int | None = None

    @model_validator(mode="after")
    def _valor_e_data_nao_ficam_vazios(self) -> "TransacaoEdicaoEntrada":
        for campo in ("valor", "data"):
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(Message.VALOR_E_DATA_OBRIGATORIOS.message)
        return self


class TransacaoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tipo: TipoTransacao
    valor: Decimal
    data: date
    descricao: str | None
    categoria_id: int | None
    origem: OrigemTransacao
    criado_em: datetime
