"""Registro, histórico e edição de transações (RF10, RF17) e lançamento automático
dos gastos fixos (RF18) e das parcelas de compras parceladas (RF37).

Este é o único módulo que grava transações (Documento de Arquitetura). Outros módulos,
como o assistente do WhatsApp, registram chamando `registrar`.
"""

import uuid
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modulos.contas import servico as servico_contas
from app.modulos.contas.esquemas import ContaAutomaticaVencida
from app.modulos.transacoes.esquemas import (
    OrigemTransacao,
    TipoTransacao,
    TransacaoEdicaoEntrada,
    TransacaoRegistroEntrada,
    TransacaoSaida,
)
from app.modulos.transacoes.modelos import Transacao
from app.nucleo import eventos

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")


class TransacaoJaRegistrada(Exception):
    """Já existe uma transação do usuário com a mesma chave externa."""


class ReferenciaInexistente(Exception):
    """O usuário ou a categoria informada não existe."""


class TransacaoNaoEncontrada(Exception):
    """A transação não existe ou é de outro usuário."""


def registrar(
    sessao: Session, usuario_id: uuid.UUID, dados: TransacaoRegistroEntrada
) -> Transacao:
    """Salva a transação e avisa o app do usuário, que atualiza saldo, indicador de
    situação e histórico sem recarregar a página (RF17)."""
    if dados.chave_externa and sessao.scalar(
        select(Transacao.id).where(
            Transacao.usuario_id == usuario_id,
            Transacao.chave_externa == dados.chave_externa,
        )
    ):
        raise TransacaoJaRegistrada

    transacao = Transacao(
        usuario_id=usuario_id,
        tipo=dados.tipo,
        valor=dados.valor,
        origem=dados.origem,
        data=dados.data or datetime.now(FUSO_BRASILIA).date(),
        descricao=dados.descricao,
        categoria_id=dados.categoria_id,
        chave_externa=dados.chave_externa,
    )
    sessao.add(transacao)
    try:
        sessao.commit()
    except IntegrityError:
        # FKs que vêm de fora: usuário e categoria
        sessao.rollback()
        raise ReferenciaInexistente from None
    sessao.refresh(transacao)
    _avisar_app(transacao)
    return transacao


def listar(sessao: Session, usuario_id: uuid.UUID) -> list[Transacao]:
    """Histórico do usuário, do lançamento mais recente para o mais antigo."""
    comando = (
        select(Transacao)
        .where(Transacao.usuario_id == usuario_id)
        .order_by(Transacao.data.desc(), Transacao.criado_em.desc())
    )
    return list(sessao.scalars(comando))


def editar(
    sessao: Session,
    usuario_id: uuid.UUID,
    transacao_id: uuid.UUID,
    dados: TransacaoEdicaoEntrada,
) -> Transacao:
    """Muda só os campos enviados. A origem fica a mesma: o lançamento automático
    editado continua marcado como automático."""
    transacao = _buscar(sessao, usuario_id, transacao_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(transacao, campo, valor)
    transacao.atualizado_em = func.now()
    try:
        sessao.commit()
    except IntegrityError:
        # Única FK que o usuário controla é a categoria
        sessao.rollback()
        raise ReferenciaInexistente from None
    sessao.refresh(transacao)
    return transacao


def excluir(sessao: Session, usuario_id: uuid.UUID, transacao_id: uuid.UUID) -> None:
    """Apaga a transação. Se ela veio de um gasto fixo, a conta continua paga, então o
    lançamento automático não volta."""
    sessao.delete(_buscar(sessao, usuario_id, transacao_id))
    sessao.commit()


def lancar_gastos_fixos(sessao: Session, hoje: date | None = None) -> int:
    """RF18 e RF37: lança como gasto cada conta fixa ou parcela que venceu até hoje e
    ainda não foi paga, com a data do vencimento, e marca a conta como paga (a conta
    fixa cria a do mês seguinte). Devolve quantos lançamentos fez. As contas vêm do
    serviço de contas: este módulo não lê a tblConta.

    Rodar de novo não duplica: a transação e o pagamento são gravados no mesmo commit, e
    a conta paga ou já ligada a uma transação não é lançada de novo. Duas execuções ao
    mesmo tempo não pegam a mesma conta (SKIP LOCKED), e o banco aceita uma só
    transação por conta (idConta único).
    """
    hoje = hoje or datetime.now(FUSO_BRASILIA).date()
    lancadas = 0
    # Contas que o usuário voltou a deixar em aberto depois do lançamento
    ja_lancadas: set[uuid.UUID] = set()
    while (
        conta := servico_contas.proxima_conta_automatica_vencida(
            sessao, hoje, ja_lancadas
        )
    ) is not None:
        if _conta_ja_lancada(sessao, conta.id):
            ja_lancadas.add(conta.id)
            continue
        transacao = Transacao(
            usuario_id=conta.usuario_id,
            tipo=TipoTransacao.SAIDA,
            valor=conta.valor,
            data=conta.vencimento_em,
            descricao=_descricao_do_lancamento(conta),
            categoria_id=conta.categoria_id,
            origem=OrigemTransacao.RECORRENTE,
            conta_id=conta.id,
        )
        sessao.add(transacao)
        servico_contas.pagar_conta_automatica(sessao, conta.id)
        sessao.commit()
        sessao.refresh(transacao)
        _avisar_app(transacao)
        lancadas += 1
    return lancadas


def _descricao_do_lancamento(conta: ContaAutomaticaVencida) -> str | None:
    """Na parcela, mostra qual é, como no extrato do cartão: "Geladeira (2/3)"."""
    if conta.parcela is None:
        return conta.descricao
    numero = f"({conta.parcela}/{conta.total_parcelas})"
    return f"{conta.descricao} {numero}" if conta.descricao else f"Parcela {numero}"


def _conta_ja_lancada(sessao: Session, conta_id: uuid.UUID) -> bool:
    return (
        sessao.scalar(select(Transacao.id).where(Transacao.conta_id == conta_id))
        is not None
    )


def _buscar(
    sessao: Session, usuario_id: uuid.UUID, transacao_id: uuid.UUID
) -> Transacao:
    """O filtro do usuario_id impede ver ou alterar a transação de outra pessoa."""
    transacao = sessao.scalar(
        select(Transacao).where(
            Transacao.id == transacao_id, Transacao.usuario_id == usuario_id
        )
    )
    if transacao is None:
        raise TransacaoNaoEncontrada
    return transacao


def _avisar_app(transacao: Transacao) -> None:
    """O app do usuário atualiza saldo, indicador de situação e histórico sem
    recarregar a página (RF17)."""
    eventos.publicar(
        transacao.usuario_id,
        eventos.TipoEvento.TRANSACAO_CRIADA,
        TransacaoSaida.model_validate(transacao).model_dump(mode="json"),
    )
