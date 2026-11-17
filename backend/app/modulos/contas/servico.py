"""Regras de cadastro e pagamento de contas a pagar (RF25, RF26, RF30)."""

import uuid
from collections.abc import Collection
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modulos.contas.esquemas import ContaCadastroEntrada, ContaFixaVencida
from app.modulos.contas.modelos import Conta
from app.modulos.contas.recorrencia import gerar_proxima_recorrencia
from app.modulos.contas.saldo import ESTRATEGIA_SALDO


class CategoriaInexistente(Exception):
    pass


class ContaNaoEncontrada(Exception):
    pass


def cadastrar(
    sessao: Session, usuario_id: uuid.UUID, dados: ContaCadastroEntrada
) -> Conta:
    """Cria a conta com status A_VENCER (calculado: sem pagamento e sem atraso)."""
    conta = Conta(
        usuario_id=usuario_id,
        vencimento_em=dados.vencimento_em,
        valor=dados.valor,
        descricao=dados.descricao,
        categoria_id=dados.categoria_id,
        recorrente=dados.recorrente,
    )
    sessao.add(conta)
    try:
        sessao.commit()
    except IntegrityError:
        # Única FK que o usuário controla é a categoria
        sessao.rollback()
        raise CategoriaInexistente from None
    sessao.refresh(conta)
    return conta


def listar(sessao: Session, usuario_id: uuid.UUID) -> list[Conta]:
    """Contas do usuário, do vencimento mais próximo para o mais distante."""
    comando = (
        select(Conta)
        .where(Conta.usuario_id == usuario_id)
        .order_by(Conta.vencimento_em)
    )
    return list(sessao.scalars(comando))


def definir_pagamento(
    sessao: Session,
    usuario_id: uuid.UUID,
    conta_id: uuid.UUID,
    paga: bool,
) -> Conta:
    """
    Marca a conta como paga ou desfaz o pagamento. Repetir 'paga=True' mantém a
    data do primeiro pagamento e repetir 'paga=False' mantém a conta pendente. O filtro
    do usuario_id impede alterar a conta de outra pessoa.
    """
    comando = (
        select(Conta)
        .where(Conta.id == conta_id, Conta.usuario_id == usuario_id)
        .with_for_update()
    )
    conta = sessao.scalar(comando)
    if conta is None:
        raise ContaNaoEncontrada

    if paga:
        registrar_pagamento(sessao, conta)
    elif conta.pagamento_em is not None:
        conta.pagamento_em = None
        ESTRATEGIA_SALDO.ao_alterar_pagamento(conta, False)

    sessao.commit()
    sessao.refresh(conta)
    return conta


def registrar_pagamento(sessao: Session, conta: Conta) -> None:
    """Marca a conta como paga; se ela é fixa, cria a do mês seguinte (RF26). Não
    grava: quem chama faz o commit. Usado também pelo lançamento automático (RF18)."""
    if conta.pagamento_em is not None:
        return
    conta.pagamento_em = datetime.now(UTC)
    ESTRATEGIA_SALDO.ao_alterar_pagamento(conta, True)
    if conta.recorrente:
        gerar_proxima_recorrencia(sessao, conta)


def proxima_conta_fixa_vencida(
    sessao: Session, hoje: date, ignorar: Collection[uuid.UUID] = ()
) -> ContaFixaVencida | None:
    """RF18: a conta fixa mais antiga que venceu até hoje e não foi paga. Fica travada
    até o commit de quem chama; outra execução ao mesmo tempo pula para a seguinte
    (SKIP LOCKED)."""
    comando = (
        select(Conta)
        .where(
            Conta.recorrente.is_(True),
            Conta.pagamento_em.is_(None),
            Conta.vencimento_em <= hoje,
            Conta.id.not_in(ignorar),
        )
        .order_by(Conta.vencimento_em)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    conta = sessao.scalar(comando)
    return ContaFixaVencida.model_validate(conta) if conta else None


def pagar_conta_fixa(sessao: Session, conta_id: uuid.UUID) -> None:
    """RF18: marca como paga a conta devolvida por `proxima_conta_fixa_vencida`. Não
    grava: quem chama faz o commit junto com o lançamento."""
    conta = sessao.get(Conta, conta_id)
    if conta is None:
        raise ContaNaoEncontrada
    registrar_pagamento(sessao, conta)
