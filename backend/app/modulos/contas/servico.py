"""Regras de cadastro e pagamento de contas a pagar (RF25, RF26, RF30)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modulos.contas.esquemas import ContaCadastroEntrada
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
