"""Registro de transações e aviso em tempo real ao app (RF17).

Este é o único módulo que grava transações (Documento de Arquitetura). Outros módulos,
como o assistente do WhatsApp, registram chamando `registrar`.
"""

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modulos.transacoes.esquemas import TransacaoRegistroEntrada, TransacaoSaida
from app.modulos.transacoes.modelos import Transacao
from app.nucleo import eventos

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")


class TransacaoJaRegistrada(Exception):
    """Já existe uma transação do usuário com a mesma chave externa."""


class ReferenciaInexistente(Exception):
    """O usuário ou a categoria informada não existe."""


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

    eventos.publicar(
        usuario_id,
        eventos.TipoEvento.TRANSACAO_CRIADA,
        TransacaoSaida.model_validate(transacao).model_dump(mode="json"),
    )
    return transacao
