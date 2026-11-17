"""Conta fixa mensal (RF26): a conta paga gera a do mês seguinte."""

from calendar import monthrange
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modulos.contas.modelos import Conta


def proximo_vencimento(base: date) -> date:
    """Mesmo dia no mês seguinte; no mês mais curto, o último dia (31/01 -> 28/02)."""
    ano = base.year + (base.month // 12)
    mes = base.month + 1 if base.month < 12 else 1
    dia = min(base.day, monthrange(ano, mes)[1])
    return date(ano, mes, dia)


def gerar_proxima_recorrencia(sessao: Session, conta_origem: Conta) -> Conta:
    """Cria a conta do mês seguinte, se ela ainda não existe. Pagar, desfazer e pagar
    de novo não gera dois meses iguais. Não grava: quem chama faz o commit."""
    id_origem = conta_origem.id_conta_origem or conta_origem.id
    vencimento = proximo_vencimento(conta_origem.vencimento_em)
    existente = sessao.scalar(
        select(Conta).where(
            Conta.id_conta_origem == id_origem, Conta.vencimento_em == vencimento
        )
    )
    if existente is not None:
        return existente

    proxima = Conta(
        usuario_id=conta_origem.usuario_id,
        vencimento_em=vencimento,
        valor=conta_origem.valor,
        descricao=conta_origem.descricao,
        categoria_id=conta_origem.categoria_id,
        recorrente=True,
        id_conta_origem=id_origem,
    )
    sessao.add(proxima)
    sessao.flush()
    return proxima
