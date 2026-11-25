"""Conta fixa mensal (RF26): a conta paga gera a do mês seguinte."""

from calendar import monthrange
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modulos.contas.modelos import Conta


def proximo_vencimento(base: date, dia: int | None = None) -> date:
    """Mês seguinte a `base`, no `dia` escolhido (padrão: o dia de `base`); no mês
    mais curto, o último dia. Com o dia da conta original, o 31 volta depois de
    fevereiro: 31/01 -> 28/02 -> 31/03 (#153)."""
    ano = base.year + (base.month // 12)
    mes = base.month + 1 if base.month < 12 else 1
    dia = min(dia or base.day, monthrange(ano, mes)[1])
    return date(ano, mes, dia)


def gerar_proxima_recorrencia(sessao: Session, conta_origem: Conta) -> Conta:
    """Cria a conta do mês seguinte, se ela ainda não existe. Pagar, desfazer e pagar
    de novo não gera dois meses iguais. Não grava: quem chama faz o commit."""
    id_origem = conta_origem.id_conta_origem or conta_origem.id
    # O dia que a pessoa escolheu é o da primeira conta, não o do mês anterior:
    # depois de fevereiro, o 28 não pode virar o dia de vencimento para sempre
    primeira = sessao.get(Conta, id_origem) or conta_origem
    vencimento = proximo_vencimento(
        conta_origem.vencimento_em, primeira.vencimento_em.day
    )
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
