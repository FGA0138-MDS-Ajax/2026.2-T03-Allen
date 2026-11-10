from calendar import monthrange
from datetime import date

from sqlalchemy.orm import Session

from app.modulos.contas.modelos import Conta


def proximo_vencimento(base: date) -> date:
    """preve qual sera a data de proximo mes"""
    ano = base.year + (base.month // 12)  # add mais um ano se tiver mais de 12 meses
    mes = base.month + 1 if base.month < 12 else 1
    dia = min(base.day, monthrange(ano, mes)[1])  # evita 31/02, 31/04...
    return date(ano, mes, dia)


def gerar_proxima_recorrencia(sessao: Session, conta_origem: Conta) -> Conta:
    proxima = Conta(
        usuario_id=conta_origem.usuario_id,
        vencimento_em=proximo_vencimento(conta_origem.vencimento_em),
        valor=conta_origem.valor,
        descricao=conta_origem.descricao,
        categoria_id=conta_origem.categoria_id,
        recorrente=True,
        id_conta_origem=conta_origem.id_conta_origem or conta_origem.id,
    )
    sessao.add(proxima)
    sessao.commit()
    sessao.refresh(proxima)
    return proxima
