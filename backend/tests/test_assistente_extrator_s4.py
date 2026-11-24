"""Regressões do extrator achadas na QA da Sprint 4 (#135, #136), com frases como a
persona Dona Lurdes escreve no WhatsApp."""

import pytest

from app.modulos.assistente.extrator import (
    TipoTransacao,
    processar_texto_mensagem,
    valor_por_extenso,
)

GASTO, RECEITA = TipoTransacao.GASTO, TipoTransacao.RECEITA


@pytest.mark.parametrize(
    ("frase", "tipo", "valor", "categoria"),
    [
        # #135: "20,5" e "2000" não são ano
        ("gastei 20,5 no onibus", GASTO, 2050, "Transporte"),
        ("gastei 2000 no conserto", GASTO, 200000, "Outros"),
        ("paguei 2015 de aluguel", GASTO, 201500, "Moradia"),
        # ... mas um ano junto de outro valor continua sendo ignorado
        ("gastei 35 em 2025 na farmacia", GASTO, 3500, "Farmácia"),
        # #135: valor por extenso
        ("gastei trinta reais no mercado", GASTO, 3000, "Alimentação"),
        ("paguei cento e vinte de luz", GASTO, 12000, "Moradia"),
        (
            "caiu mil quinhentos e dezoito da aposentadoria",
            RECEITA,
            151800,
            "Aposentadoria",
        ),
        ("comprei dois paes por dez reais", GASTO, 1000, "Alimentação"),
        # #136: alguém deu ou pagou para a pessoa
        ("o neto me deu 50", RECEITA, 5000, "Outras Receitas"),
        ("meu filho me pagou 200", RECEITA, 20000, "Outras Receitas"),
        ("vendi um bolo por 30", RECEITA, 3000, "Renda Extra"),
        # ... sem mudar os gastos com "deu" e "paguei"
        ("deu 18,50 na drogaria", GASTO, 1850, "Farmácia"),
        ("paguei 150 na consulta com o médico", GASTO, 15000, "Saúde"),
    ],
)
def test_frases_da_persona(frase, tipo, valor, categoria):
    r = processar_texto_mensagem(frase)
    assert (r.sucesso, r.tipo, r.valor, r.categoria) == (True, tipo, valor, categoria)


@pytest.mark.parametrize(
    "frase", ["comprei um remedio", "comprei dois paes", "gastei na farmácia"]
)
def test_artigo_e_quantidade_nao_viram_valor(frase):
    """ "um remédio" não é R$ 1,00: o assistente pede o valor (RF16)."""
    r = processar_texto_mensagem(frase)
    assert r.valor is None
    assert r.motivo_recusa == "sem_valor"


@pytest.mark.parametrize(
    ("texto", "centavos"),
    [
        ("trinta", 3000),
        ("vinte e um", 2100),
        ("cem", 10000),
        ("mil e quinhentos", 150000),
        ("dois mil reais", 200000),
        ("um real", 100),
        ("uma", None),
        ("nada", None),
    ],
)
def test_valor_por_extenso(texto, centavos):
    assert valor_por_extenso(texto) == centavos


def test_gasto_nao_cai_em_categoria_de_entrada():
    r = processar_texto_mensagem("paguei 30 na venda do seu ze")
    assert r.tipo == GASTO
    assert r.categoria not in {"Aposentadoria", "Salário", "Renda Extra"}
