"""RF16: quando o assistente não consegue extrair valor, tipo ou categoria, explica o
motivo em linguagem simples e pede só o dado que falta. Nenhum lançamento é perdido
em silêncio."""

from decimal import Decimal

import fakeredis
import pytest

from app.modulos.assistente import mensagens
from app.modulos.assistente.extrator import TipoTransacao, identificar_tipo_resposta
from app.modulos.assistente.sessao import CampoFaltando, GerenciadorSessao
from tests.test_assistente_rf12_rf15 import ambiente_assistente  # noqa: F401


def test_sem_valor_explica_e_pede_so_o_valor(ambiente_assistente):  # noqa: F811
    sessao, telefone, enviadas, registrar, enviar = ambiente_assistente

    enviar("gastei na farmácia")

    assert "Não consegui entender o valor" in enviadas[-1]
    assert "Quanto foi esse gasto com Farmácia?" in enviadas[-1]
    pendencia, _ = sessao.obter_pendencia(telefone)
    assert pendencia.faltando == CampoFaltando.VALOR
    assert pendencia.valor is None

    enviar("35")

    assert enviadas[-1] == mensagens.confirmacao_gasto(3500, "Farmácia")
    assert sessao.obter_pendencia(telefone)[0].faltando is None
    assert registrar.call_count == 0

    enviar("Sim")

    assert registrar.call_count == 1
    assert registrar.call_args.kwargs["dados"].valor == Decimal("35.00")
    assert registrar.call_args.kwargs["dados"].descricao == "gastei na farmácia"


def test_resposta_sem_valor_pergunta_de_novo_sem_perder(ambiente_assistente):  # noqa: F811
    sessao, telefone, enviadas, registrar, enviar = ambiente_assistente

    enviar("paguei a luz")
    enviar("não lembro direito")

    assert enviadas[-1] == mensagens.valor_ainda_nao_entendido()
    pendencia, _ = sessao.obter_pendencia(telefone)
    assert pendencia is not None
    assert pendencia.faltando == CampoFaltando.VALOR
    assert pendencia.categoria == "Moradia"

    enviar("120,50")

    assert enviadas[-1] == mensagens.confirmacao_gasto(12050, "Moradia")


def test_receita_sem_valor(ambiente_assistente):  # noqa: F811
    _, _, enviadas, _, enviar = ambiente_assistente

    enviar("recebi a aposentadoria")

    assert "Quanto foi essa entrada de Aposentadoria?" in enviadas[-1]


def test_cancelar_durante_o_preenchimento(ambiente_assistente):  # noqa: F811
    sessao, telefone, enviadas, registrar, enviar = ambiente_assistente

    enviar("gastei no mercado")
    enviar("cancelar")

    assert enviadas[-1] == mensagens.registro_cancelado()
    assert sessao.obter_pendencia(telefone)[0] is None
    assert registrar.call_count == 0


@pytest.mark.parametrize(
    ("frase", "esperada"),
    [
        ("vou gastar 100 amanhã", mensagens.explicar_futuro()),
        ("gastei 35 na farmácia e 20 na padaria", mensagens.explicar_varios_valores()),
    ],
)
def test_recusa_explica_o_motivo(ambiente_assistente, frase, esperada):  # noqa: F811
    sessao, telefone, enviadas, _, enviar = ambiente_assistente

    enviar(frase)

    assert enviadas == [esperada]
    assert sessao.obter_pendencia(telefone)[0] is None


def test_falha_no_banco_nao_diz_anotado(ambiente_assistente):  # noqa: F811
    sessao, telefone, enviadas, registrar, enviar = ambiente_assistente
    registrar.side_effect = RuntimeError("banco fora do ar")

    enviar("gastei 35 na farmácia")
    enviar("Sim")

    assert enviadas[-1] == mensagens.falha_ao_salvar()
    pendencia, _ = sessao.obter_pendencia(telefone)
    assert pendencia is not None
    assert pendencia.valor == 3500

    registrar.side_effect = None
    enviar("Sim")

    assert registrar.call_count == 2
    assert enviadas[-1] == mensagens.confirmacao_sucesso_gasto(3500, "Farmácia")
    assert sessao.obter_pendencia(telefone)[0] is None


def test_pergunta_tipo_e_categoria_quando_faltam(ambiente_assistente):  # noqa: F811
    """Ex.: foto em que só o valor foi lido. Categoria vazia = não identificada."""
    sessao, telefone, enviadas, registrar, enviar = ambiente_assistente
    sessao.salvar_pendencia(
        telefone,
        TipoTransacao.DESCONHECIDO,
        5000,
        "",
        "",
        faltando=CampoFaltando.TIPO,
    )

    enviar("sei lá")
    assert enviadas[-1] == mensagens.tipo_ainda_nao_entendido()

    enviar("foi gasto")
    assert enviadas[-1] == mensagens.pedir_categoria(False, 5000)
    assert sessao.obter_pendencia(telefone)[0].faltando == CampoFaltando.CATEGORIA

    enviar("mercado")
    assert enviadas[-1] == mensagens.confirmacao_gasto(5000, "Alimentação")

    enviar("sim")
    assert registrar.call_args.kwargs["dados"].valor == Decimal("50.00")


def test_categoria_desconhecida_fica_em_outros(ambiente_assistente):  # noqa: F811
    sessao, telefone, enviadas, _, enviar = ambiente_assistente
    sessao.salvar_pendencia(
        telefone,
        TipoTransacao.GASTO,
        5000,
        "",
        "",
        faltando=CampoFaltando.CATEGORIA,
    )

    enviar("conserto do portão")

    assert enviadas[-1] == mensagens.confirmacao_gasto(5000, "Outros")
    assert sessao.obter_pendencia(telefone)[0].descricao == "conserto do portão"


@pytest.mark.parametrize(
    ("texto", "tipo"),
    [
        ("gasto", TipoTransacao.GASTO),
        ("Foi uma saída", TipoTransacao.GASTO),
        ("entrada", TipoTransacao.RECEITA),
        ("eu recebi", TipoTransacao.RECEITA),
        ("não sei", TipoTransacao.DESCONHECIDO),
    ],
)
def test_identifica_resposta_gasto_ou_entrada(texto, tipo):
    assert identificar_tipo_resposta(texto) == tipo


def test_rascunho_incompleto_sobrevive_no_valkey():
    sessao = GerenciadorSessao()
    sessao._valkey = fakeredis.FakeRedis(decode_responses=True)
    tel = "5561988887777"

    sessao.salvar_pendencia(
        tel,
        TipoTransacao.GASTO,
        None,
        "Farmácia",
        "gastei na farmácia",
        faltando=CampoFaltando.VALOR,
    )
    pendencia, expirou = sessao.obter_pendencia(tel)

    assert expirou is False
    assert pendencia.valor is None
    assert pendencia.faltando == CampoFaltando.VALOR
    assert tel not in sessao._sessoes_memoria
