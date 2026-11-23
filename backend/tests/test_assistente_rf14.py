"""RF14: o assistente lê a foto de um comprovante, nota fiscal ou conta. O que a foto
não trouxe, ele pede à pessoa (RF16). A imagem não é guardada (LGPD)."""

import asyncio
import base64
import logging
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient

import app.modulos.assistente.router as router_module
from app.integracoes import leitor_comprovante
from app.main import app
from app.modulos.assistente import mensagens
from app.modulos.assistente.sessao import CampoFaltando
from app.modulos.transacoes.esquemas import OrigemTransacao
from app.nucleo.config import settings
from app.nucleo.portas import FalhaLeituraComprovante, LeituraComprovante
from tests.test_assistente_rf12_rf15 import ambiente_assistente  # noqa: F401

FOTO = b"\xff\xd8\xff\xe0 foto de teste"


def _mensagem_com_foto(legenda: str | None = None) -> dict:
    imagem = {"mimetype": "image/jpeg"}
    if legenda:
        imagem["caption"] = legenda
    return {
        "key": {"id": "ABC123", "remoteJid": "5561999999999@s.whatsapp.net"},
        "message": {
            "imageMessage": imagem,
            "base64": base64.b64encode(FOTO).decode(),
        },
    }


@pytest.fixture
def leitor(monkeypatch):
    """Leitor que devolve a leitura escolhida pelo teste e guarda o que recebeu."""
    falso = SimpleNamespace(leitura=LeituraComprovante(), recebido=None)

    async def ler(imagem, tipo_mime, legenda):
        falso.recebido = (imagem, tipo_mime, legenda)
        if isinstance(falso.leitura, Exception):
            raise falso.leitura
        return falso.leitura

    monkeypatch.setattr(
        router_module, "obter_leitor_comprovante", lambda: SimpleNamespace(ler=ler)
    )
    return falso


def _enviar_foto(legenda: str | None = None):
    remetente = "5561999999999@s.whatsapp.net"
    asyncio.run(router_module.processar_foto(remetente, _mensagem_com_foto(legenda)))


def test_foto_lida_pede_confirmacao_e_grava_como_foto(ambiente_assistente, leitor):  # noqa: F811
    _, _, enviadas, registrar, enviar = ambiente_assistente
    leitor.leitura = LeituraComprovante(
        valor=4590, tipo="GASTO", categoria="Farmácia", descricao="Drogaria Rosário"
    )

    _enviar_foto("remédio da pressão")

    assert leitor.recebido == (FOTO, "image/jpeg", "remédio da pressão")
    assert enviadas[-1] == mensagens.confirmacao_gasto(4590, "Farmácia")

    enviar("Sim")

    dados = registrar.call_args.kwargs["dados"]
    assert dados.valor == Decimal("45.90")
    assert dados.origem == OrigemTransacao.WHATSAPP_FOTO
    assert dados.descricao == "Drogaria Rosário"


def test_foto_de_pix_recebido(ambiente_assistente, leitor):  # noqa: F811
    _, _, enviadas, registrar, enviar = ambiente_assistente
    leitor.leitura = LeituraComprovante(
        valor=150000, tipo="RECEITA", categoria="Aposentadoria"
    )

    _enviar_foto()
    enviar("Sim")

    assert enviadas[0] == mensagens.confirmacao_renda(150000, "Aposentadoria")
    assert registrar.call_args.kwargs["dados"].tipo == "entrada"


def test_foto_sem_valor_explica_e_pede_o_valor(ambiente_assistente, leitor):  # noqa: F811
    sessao, telefone, enviadas, registrar, enviar = ambiente_assistente
    leitor.leitura = LeituraComprovante(tipo="GASTO", categoria="Moradia")

    _enviar_foto()

    assert enviadas[-1].startswith("Não consegui ler o valor na foto.")
    pendencia, _ = sessao.obter_pendencia(telefone)
    assert pendencia.faltando == CampoFaltando.VALOR

    enviar("98,70")
    assert enviadas[-1] == mensagens.confirmacao_gasto(9870, "Moradia")

    enviar("sim")
    dados = registrar.call_args.kwargs["dados"]
    assert dados.valor == Decimal("98.70")
    assert dados.origem == OrigemTransacao.WHATSAPP_FOTO


def test_foto_ilegivel_pede_cada_dado_sem_perder(ambiente_assistente, leitor):  # noqa: F811
    _, _, enviadas, registrar, enviar = ambiente_assistente
    leitor.leitura = FalhaLeituraComprovante("fora do ar")

    _enviar_foto()
    assert enviadas[-1].startswith("Não consegui ler o valor na foto.")

    enviar("30")
    assert enviadas[-1] == mensagens.pedir_tipo(3000)

    enviar("gasto")
    assert enviadas[-1] == mensagens.pedir_categoria(False, 3000)

    enviar("padaria")
    assert enviadas[-1] == mensagens.confirmacao_gasto(3000, "Alimentação")

    enviar("sim")
    assert registrar.call_args.kwargs["dados"].origem == OrigemTransacao.WHATSAPP_FOTO


def test_foto_sem_categoria_pergunta_com_o_que_foi(ambiente_assistente, leitor):  # noqa: F811
    _, _, enviadas, _, _ = ambiente_assistente
    leitor.leitura = LeituraComprovante(valor=2000, tipo="GASTO")

    _enviar_foto()

    assert enviadas[-1] == mensagens.pedir_categoria(
        False, 2000, "Não consegui saber pela foto com o que foi."
    )


def test_falha_ao_baixar_a_foto_cai_no_preenchimento(
    ambiente_assistente,  # noqa: F811
    leitor,
    monkeypatch,
):
    _, _, enviadas, _, _ = ambiente_assistente

    async def falhar(_):
        raise httpx.ConnectError("sem conexão")

    monkeypatch.setattr(router_module, "baixar_imagem", falhar)

    _enviar_foto()

    assert enviadas[-1].startswith("Não consegui ler o valor na foto.")
    assert leitor.recebido is None


def test_tempo_da_foto_vai_para_o_log_sem_dados(ambiente_assistente, leitor, caplog):  # noqa: F811
    leitor.leitura = LeituraComprovante(valor=4590, tipo="GASTO", categoria="Farmácia")

    with caplog.at_level(logging.INFO, logger=router_module.logger.name):
        _enviar_foto("remédio")

    registros = [r.getMessage() for r in caplog.records]
    assert any(r.startswith("Foto processada em ") for r in registros)
    assert not any("45" in r or "remédio" in r for r in registros)


def test_baixar_imagem_do_base64_do_webhook():
    dados = _mensagem_com_foto()
    dados["message"]["base64"] = (
        "data:image/png;base64," + base64.b64encode(FOTO).decode()
    )
    dados["message"]["imageMessage"]["mimetype"] = "image/png"

    imagem, tipo = asyncio.run(router_module.baixar_imagem(dados))

    assert imagem == FOTO
    assert tipo == "image/png"


def test_webhook_manda_foto_para_a_leitura(monkeypatch):
    recebidas = []

    async def processar_foto(remetente, dados):
        recebidas.append((remetente, dados))

    monkeypatch.setattr(router_module, "processar_foto", processar_foto)
    payload = {"event": "messages.upsert", "data": _mensagem_com_foto()}

    with TestClient(app) as cliente:
        resposta = cliente.post(
            "/webhook/whatsapp",
            json=payload,
            headers={"apikey": settings.AUTHENTICATION_API_KEY},
        )

    assert resposta.status_code == 200
    assert recebidas[0][0] == "5561999999999@s.whatsapp.net"


# Adaptador da API do Claude


def _leitor_claude(monkeypatch, parse: AsyncMock):
    leitor = leitor_comprovante.LeitorComprovanteClaude()
    monkeypatch.setattr(leitor._cliente.messages, "parse", parse)
    return leitor


def _resposta(**campos) -> SimpleNamespace:
    leitura = leitor_comprovante._Leitura(
        **{
            "valor_centavos": None,
            "tipo": "DESCONHECIDO",
            "categoria": "DESCONHECIDA",
            "descricao": "",
            **campos,
        }
    )
    return SimpleNamespace(stop_reason="end_turn", parsed_output=leitura)


def test_claude_le_e_limpa_a_resposta(monkeypatch):
    parse = AsyncMock(
        return_value=_resposta(
            valor_centavos=3590,
            tipo="gasto",
            categoria="Farmácia",
            descricao="  Drogaria  ",
        )
    )
    leitor = _leitor_claude(monkeypatch, parse)

    leitura = asyncio.run(leitor.ler(FOTO, "image/jpeg", "remédio"))

    assert leitura == LeituraComprovante(
        valor=3590, tipo="GASTO", categoria="Farmácia", descricao="Drogaria"
    )
    argumentos = parse.call_args.kwargs
    assert argumentos["model"] == settings.AI_MODELO
    imagem = argumentos["messages"][0]["content"][0]
    assert imagem["source"]["data"] == base64.standard_b64encode(FOTO).decode()
    assert "remédio" in argumentos["messages"][0]["content"][1]["text"]


def test_claude_descarta_o_que_nao_faz_sentido(monkeypatch):
    parse = AsyncMock(
        return_value=_resposta(valor_centavos=0, tipo="talvez", categoria="Pets")
    )
    leitor = _leitor_claude(monkeypatch, parse)

    leitura = asyncio.run(leitor.ler(FOTO, "image/jpeg", None))

    assert leitura == LeituraComprovante()


def test_claude_fora_do_ar_vira_falha_de_leitura(monkeypatch):
    erro = anthropic.APITimeoutError(request=httpx.Request("POST", "https://x"))
    leitor = _leitor_claude(monkeypatch, AsyncMock(side_effect=erro))

    with pytest.raises(FalhaLeituraComprovante):
        asyncio.run(leitor.ler(FOTO, "image/jpeg", None))


def test_claude_recusa_formato_nao_aceito(monkeypatch):
    parse = AsyncMock()
    leitor = _leitor_claude(monkeypatch, parse)

    with pytest.raises(FalhaLeituraComprovante):
        asyncio.run(leitor.ler(FOTO, "application/pdf", None))
    parse.assert_not_called()
