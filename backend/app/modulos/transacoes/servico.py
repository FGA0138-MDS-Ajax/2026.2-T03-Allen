"""Registro, histórico e edição de transações (RF10, RF17).

Este é o único módulo que grava transações (Documento de Arquitetura). Outros módulos,
como o assistente do WhatsApp, registram chamando `registrar`.
"""

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modulos.transacoes.esquemas import (
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
