"""Rotas de investimentos (RF35)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.seguranca import usuario_atual
from app.modulos.investimentos import servico
from app.modulos.investimentos.esquemas import (
    InvestimentoCadastroEntrada,
    InvestimentoSaida,
)
from app.modulos.investimentos.modelos import Investimento
from app.nucleo.banco import obter_sessao

router = APIRouter(prefix="/api/v1/investimentos", tags=["investimentos"])


@router.post("", response_model=InvestimentoSaida, status_code=status.HTTP_201_CREATED)
def cadastrar(
    dados: InvestimentoCadastroEntrada,
    usuario: Usuario = Depends(usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Investimento:
    return servico.cadastrar(sessao, usuario.id, dados)


@router.get("", response_model=list[InvestimentoSaida])
def listar(
    usuario: Usuario = Depends(usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> list[Investimento]:
    return servico.listar(sessao, usuario.id)
