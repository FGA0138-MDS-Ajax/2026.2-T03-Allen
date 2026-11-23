"""#138: o gasto confirmado no WhatsApp é gravado com a categoria do app."""

import asyncio
from contextlib import nullcontext

import pytest
from sqlalchemy import select

import app.modulos.assistente.router as router_module
from app.modulos.assistente.sessao import GerenciadorSessao
from app.modulos.contas.modelos import Categoria
from app.modulos.transacoes.modelos import Transacao


@pytest.fixture
def conversa(monkeypatch, sessao, usuario):
    for nome in ["Moradia", "Alimentação", "Saúde", "Transporte", "Lazer", "Outros"]:
        sessao.add(Categoria(nome=nome))
    sessao.flush()

    gerenciador = GerenciadorSessao()
    gerenciador._valkey = None
    monkeypatch.setattr(router_module, "sessao_assistente", gerenciador)
    monkeypatch.setattr(router_module, "buscar_usuario_telefone", lambda _: usuario)
    monkeypatch.setattr(router_module, "SessaoLocal", lambda: nullcontext(sessao))

    async def enviar(_, texto):
        pass

    monkeypatch.setattr(router_module, "enviar_mensagem", enviar)

    def dizer(*textos):
        for texto in textos:
            asyncio.run(
                router_module.processar_responder(
                    f"{usuario.telefone}@s.whatsapp.net", texto
                )
            )

    def ultima():
        return sessao.scalars(
            select(Transacao)
            .where(Transacao.usuario_id == usuario.id)
            .order_by(Transacao.criado_em.desc())
        ).first()

    def categoria(nome):
        return sessao.scalar(select(Categoria.id).where(Categoria.nome == nome))

    return dizer, ultima, categoria


@pytest.mark.parametrize(
    ("frase", "categoria_app"),
    [
        ("gastei 30 conto na farmasia", "Saúde"),
        ("paguei 120 de luz", "Moradia"),
        ("gastei 50 no mercado", "Alimentação"),
        ("gastei 40 no conserto", "Outros"),
    ],
)
def test_gasto_sai_com_a_categoria_do_app(conversa, frase, categoria_app):
    dizer, ultima, categoria = conversa

    dizer(frase, "sim")

    assert ultima().categoria_id == categoria(categoria_app)


def test_entrada_fica_sem_categoria(conversa):
    dizer, ultima, _ = conversa

    dizer("recebi 1518 da aposentadoria", "sim")

    assert ultima().tipo == "entrada"
    assert ultima().categoria_id is None
