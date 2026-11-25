"""RF23: resposta do assistente à pergunta sobre o saldo disponível do mês."""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import app.modulos.assistente.router as router_module
from app.modulos.assistente import mensagens
from tests.test_assistente_rf12_rf15 import ambiente_assistente  # noqa: F401


@pytest.mark.parametrize(
    "pergunta",
    [
        "quanto eu tenho?",
        "qual meu saldo?",
        "quanto tenho disponível?",
        "quanto sobrou?",
        "tenho dinheiro?",
    ],
)
def test_pergunta_saldo_retorna_disponivel_do_mes(
    ambiente_assistente,  # noqa: F811
    monkeypatch,
    pergunta,
):
    _, _, enviadas, _, enviar = ambiente_assistente
    resumir_mes = Mock(return_value=SimpleNamespace(saldo=Decimal("1234.56")))
    monkeypatch.setattr(router_module.servico_transacoes, "resumir_mes", resumir_mes)

    enviar(pergunta)

    mes_atual = datetime.now(router_module.servico_transacoes.FUSO_BRASILIA).strftime(
        "%Y-%m"
    )
    resumir_mes.assert_called_once()
    assert resumir_mes.call_args.args[1:] == ("usuario-teste", mes_atual)
    assert enviadas == [mensagens.resposta_saldo(Decimal("1234.56"))]


def test_pergunta_saldo_negativo_tem_resposta_simples(  # noqa: F811
    ambiente_assistente,  # noqa: F811
    monkeypatch,
):
    _, _, enviadas, _, enviar = ambiente_assistente
    monkeypatch.setattr(
        router_module.servico_transacoes,
        "resumir_mes",
        Mock(return_value=SimpleNamespace(saldo=Decimal("-25.00"))),
    )

    enviar("qual meu saldo?")

    assert enviadas == ["Neste mês, faltam *R$ 25,00* para cobrir suas despesas."]


def test_pergunta_saldo_preserva_lancamento_pendente(  # noqa: F811
    ambiente_assistente,  # noqa: F811
    monkeypatch,
):
    sessao, telefone, enviadas, registrar, enviar = ambiente_assistente
    monkeypatch.setattr(
        router_module.servico_transacoes,
        "resumir_mes",
        Mock(return_value=SimpleNamespace(saldo=Decimal("50.00"))),
    )

    enviar("gastei 10 no mercado")
    pendencia_antes, _ = sessao.obter_pendencia(telefone)
    enviar("qual meu saldo?")
    pendencia_depois, _ = sessao.obter_pendencia(telefone)

    assert enviadas[-1] == "Você tem *R$ 50,00* disponíveis neste mês."
    assert pendencia_depois == pendencia_antes
    assert registrar.call_count == 0


@pytest.mark.parametrize(
    "frase",
    [
        "gastei 30 no mercado com o saldo do cartão",
        "recebi 200, agora tenho dinheiro",
        "paguei 50 do disponível",
    ],
)
def test_mensagem_com_valor_nao_e_pergunta_de_saldo(
    ambiente_assistente,  # noqa: F811
    monkeypatch,
    frase,
):
    _, _, _, _, enviar = ambiente_assistente
    resumir_mes = Mock()
    monkeypatch.setattr(router_module.servico_transacoes, "resumir_mes", resumir_mes)

    enviar(frase)

    resumir_mes.assert_not_called()
