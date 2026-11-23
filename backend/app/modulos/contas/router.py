"""Rotas de contas a pagar (RF25, RF30)."""

import unicodedata
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modulos.contas import servico
from app.modulos.contas.esquemas import (
    CategoriaSaida,
    ContaCadastroEntrada,
    ContaPagamentoEntrada,
    ContaSaida,
)
from app.modulos.contas.mensagens import Message
from app.modulos.contas.modelos import Categoria, Conta
from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.seguranca import usuario_atual
from app.nucleo.banco import obter_sessao

router = APIRouter(prefix="/api/v1/contas", tags=["contas"])
categorias_router = APIRouter(prefix="/api/v1/categorias", tags=["categorias"])

# Tradução de categorias entre front-end e back-end
_CODIGOS_POR_NOME = {
    "moradia" : "casa",
    "alimentacao" : "mercado",
    "saude" : "farmacia",
}

def _codigo_categoria(nome: str) -> str:
    normalizado = unicodedata.normalize("NFKD", nome.casefold())
    sem_acentos = "".join(
        caractere
        for caractere in normalizado
        if not unicodedata.combining(caractere)
    )
    return _CODIGOS_POR_NOME.get(
        sem_acentos,
        sem_acentos.replace(" ", "_"),
    )

@router.post("", response_model=ContaSaida, status_code=status.HTTP_201_CREATED)
def cadastrar(
    dados: ContaCadastroEntrada,
    usuario: Usuario = Depends(usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Conta:
    try:
        return servico.cadastrar(sessao, usuario.id, dados)
    except servico.CategoriaInexistente:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            Message.CATEGORIA_INEXISTENTE.message,
        ) from None

@categorias_router.get("", response_model=list[CategoriaSaida])
def listar_categorias(
    usuario: Usuario = Depends(usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> list[CategoriaSaida]:
    categorias = sessao.scalars(
        select(Categoria).order_by(Categoria.id)
    )

    return [
        CategoriaSaida(
            id=categoria.id,
            codigo=_codigo_categoria(categoria.nome),
            nome=categoria.nome,
        )
        for categoria in categorias
    ]

@router.get("", response_model=list[ContaSaida])
def listar(
    usuario: Usuario = Depends(usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> list[Conta]:
    return servico.listar(sessao, usuario.id)


@router.patch("/{conta_id}/pagamento", response_model=ContaSaida)
def definir_pagamento(
    conta_id: UUID,
    dados: ContaPagamentoEntrada,
    usuario: Usuario = Depends(usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Conta:
    try:
        return servico.definir_pagamento(sessao, usuario.id, conta_id, dados.paga)
    except servico.ContaNaoEncontrada:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            Message.CONTA_NAO_ENCONTRADA.message,
        ) from None
