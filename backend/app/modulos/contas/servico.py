"""Regras de cadastro e pagamento de contas a pagar (RF25, RF26, RF30, RF37)."""

import uuid
from collections.abc import Collection
from datetime import UTC, date, datetime

from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modulos.contas.esquemas import (
    ContaAutomaticaVencida,
    ContaAVencer,
    ContaCadastroEntrada,
)
from app.modulos.contas.modelos import Conta
from app.modulos.contas.parcelas import datas_das_parcelas, dividir_valor
from app.modulos.contas.recorrencia import gerar_proxima_recorrencia
from app.modulos.contas.saldo import ESTRATEGIA_SALDO


class CategoriaInexistente(Exception):
    pass


class ContaNaoEncontrada(Exception):
    pass


def cadastrar(
    sessao: Session, usuario_id: uuid.UUID, dados: ContaCadastroEntrada
) -> Conta:
    """Cria a conta com status A_VENCER (calculado: sem pagamento e sem atraso). Na
    compra parcelada (RF37), cria uma conta por parcela e devolve a 1ª."""
    if dados.parcelas:
        contas = _parcelas_da_compra(usuario_id, dados)
    else:
        contas = [
            Conta(
                usuario_id=usuario_id,
                vencimento_em=dados.vencimento_em,
                valor=dados.valor,
                descricao=dados.descricao,
                categoria_id=dados.categoria_id,
                recorrente=dados.recorrente,
            )
        ]
    sessao.add_all(contas)
    try:
        sessao.commit()
    except IntegrityError:
        # Única FK que o usuário controla é a categoria
        sessao.rollback()
        raise CategoriaInexistente from None
    sessao.refresh(contas[0])
    return contas[0]


def _parcelas_da_compra(
    usuario_id: uuid.UUID, dados: ContaCadastroEntrada
) -> list[Conta]:
    """Uma conta por parcela, a partir do mês seguinte ao da compra. As demais ficam
    ligadas à 1ª pela idContaOrigem."""
    total = dados.parcelas
    primeira_id = uuid.uuid4()
    return [
        Conta(
            id=primeira_id if numero == 1 else uuid.uuid4(),
            usuario_id=usuario_id,
            vencimento_em=vencimento,
            valor=valor,
            descricao=dados.descricao,
            categoria_id=dados.categoria_id,
            id_conta_origem=None if numero == 1 else primeira_id,
            parcela=numero,
            total_parcelas=total,
        )
        for numero, (vencimento, valor) in enumerate(
            zip(
                datas_das_parcelas(dados.vencimento_em, total),
                dividir_valor(dados.valor, total),
                strict=True,
            ),
            start=1,
        )
    ]


class ContaJaLancada(Exception):
    """A conta já gerou uma transação (gasto fixo ou parcela lançada)."""


def excluir(sessao: Session, usuario_id: uuid.UUID, conta_id: uuid.UUID) -> None:
    """Apaga a conta (#133). Só a do próprio usuário. Os meses seguintes e as outras
    parcelas que apontam para ela ficam de pé, sem o vínculo. Conta que já virou
    gasto no extrato não é apagada: a pessoa apaga o gasto antes."""
    conta = sessao.scalar(
        select(Conta).where(Conta.id == conta_id, Conta.usuario_id == usuario_id)
    )
    if conta is None:
        raise ContaNaoEncontrada
    sessao.execute(
        update(Conta)
        .where(Conta.id_conta_origem == conta.id)
        .values(id_conta_origem=None)
    )
    sessao.delete(conta)
    try:
        sessao.commit()
    except IntegrityError:
        # FK da tblTransacao.idConta: o lançamento automático já existe
        sessao.rollback()
        raise ContaJaLancada from None


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


def proxima_conta_automatica_vencida(
    sessao: Session, hoje: date, ignorar: Collection[uuid.UUID] = ()
) -> ContaAutomaticaVencida | None:
    """RF18 e RF37: a conta fixa ou parcela mais antiga que venceu até hoje e não foi
    paga. Fica travada até o commit de quem chama; outra execução ao mesmo tempo pula
    para a seguinte (SKIP LOCKED)."""
    comando = (
        select(Conta)
        .where(
            or_(Conta.recorrente.is_(True), Conta.total_parcelas.is_not(None)),
            Conta.pagamento_em.is_(None),
            Conta.vencimento_em <= hoje,
            Conta.id.not_in(ignorar),
        )
        .order_by(Conta.vencimento_em)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    conta = sessao.scalar(comando)
    return ContaAutomaticaVencida.model_validate(conta) if conta else None


def pagar_conta_automatica(sessao: Session, conta_id: uuid.UUID) -> None:
    """RF18 e RF37: marca como paga a conta devolvida por
    `proxima_conta_automatica_vencida`. Não grava: quem chama faz o commit junto com o
    lançamento."""
    conta = sessao.get(Conta, conta_id)
    if conta is None:
        raise ContaNaoEncontrada
    registrar_pagamento(sessao, conta)


def contas_em_aberto_entre(
    sessao: Session, inicio: date, fim: date
) -> list[ContaAVencer]:
    """RF28 e RF29: contas não pagas que vencem entre as datas (inclusive), da que vence
    primeiro para a última."""
    comando = (
        select(Conta)
        .where(
            Conta.pagamento_em.is_(None),
            Conta.vencimento_em >= inicio,
            Conta.vencimento_em <= fim,
        )
        .order_by(Conta.vencimento_em, Conta.criado_em)
    )
    return [ContaAVencer.model_validate(conta) for conta in sessao.scalars(comando)]
def id_da_categoria(sessao: Session, nome: str) -> int | None:
    """Id da categoria com esse nome na tblCategoria, ou None se não existir."""
    return sessao.scalar(select(Categoria.id).where(Categoria.nome == nome))
