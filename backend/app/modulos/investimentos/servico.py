"""Regras de cadastro e consulta de investimentos (RF35)."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modulos.investimentos.esquemas import InvestimentoCadastroEntrada
from app.modulos.investimentos.modelos import Investimento


def cadastrar(
    sessao: Session, usuario_id: uuid.UUID, dados: InvestimentoCadastroEntrada
) -> Investimento:
    investimento = Investimento(usuario_id=usuario_id, **dados.model_dump())
    sessao.add(investimento)
    sessao.commit()
    sessao.refresh(investimento)
    return investimento


def listar(sessao: Session, usuario_id: uuid.UUID) -> list[Investimento]:
    """Investimentos do usuário, da aplicação mais recente para a mais antiga."""
    comando = (
        select(Investimento)
        .where(Investimento.usuario_id == usuario_id)
        .order_by(Investimento.aplicado_em.desc(), Investimento.criado_em.desc())
    )
    return list(sessao.scalars(comando))
