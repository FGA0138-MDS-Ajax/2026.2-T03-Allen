"""Compra parcelada (RF37): divide o valor e escolhe a data de cada parcela, como na
fatura do cartão."""

from calendar import monthrange
from datetime import date
from decimal import Decimal
from enum import Enum

CENTAVO = Decimal("0.01")


class Parcelamento(Enum):
    """Limites do número de parcelas."""

    MINIMO = 2
    MAXIMO = 24


def dividir_valor(total: Decimal, parcelas: int) -> list[Decimal]:
    """Valor de cada parcela. Os centavos que sobram vão na 1ª, como nas lojas e nos
    cartões: R$ 100,00 em 3x = 33,34 + 33,33 + 33,33."""
    centavos = int(total / CENTAVO)
    base, sobra = divmod(centavos, parcelas)
    valores = [Decimal(base) * CENTAVO] * parcelas
    valores[0] = Decimal(base + sobra) * CENTAVO
    return valores


def somar_meses(base: date, meses: int) -> date:
    """Mesmo dia, `meses` depois. No mês mais curto, o último dia; o dia da compra não se
    perde nos meses seguintes (31/01 -> 28/02 -> 31/03)."""
    indice = base.month - 1 + meses
    ano, mes = base.year + indice // 12, indice % 12 + 1
    return date(ano, mes, min(base.day, monthrange(ano, mes)[1]))


def datas_das_parcelas(compra: date, parcelas: int) -> list[date]:
    """A 1ª parcela vence no mês seguinte ao da compra, como na fatura do cartão."""
    return [somar_meses(compra, numero) for numero in range(1, parcelas + 1)]
