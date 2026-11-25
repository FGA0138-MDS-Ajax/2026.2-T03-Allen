"""Testes do cadastro de investimentos (RF35)."""

import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.seguranca import criar_token
from app.modulos.investimentos.esquemas import FUSO_BRASILIA
from app.modulos.investimentos.mensagens import Message

HOJE = datetime.now(FUSO_BRASILIA).date()


def _cdb(**mudancas) -> dict:
    dados = {
        "tipo": "cdb",
        "nome": "CDB do Banco do Brasil",
        "instituicao": "Banco do Brasil",
        "valor_aplicado": "5000.00",
        "aplicado_em": "2026-03-10",
        "vence_em": "2028-03-10",
        "indexador": "cdi",
        "taxa": "110",
        "liquidez_diaria": False,
    }
    dados.update(mudancas)
    return dados


def _erros(resposta) -> list[dict]:
    assert resposta.status_code == 422, resposta.text
    return resposta.json()["erros"]


def test_cadastra_cdb_com_os_dados_do_banco(cliente_logado: TestClient) -> None:
    resposta = cliente_logado.post("/api/v1/investimentos", json=_cdb())

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert {k: corpo[k] for k in _cdb()} == {
        "tipo": "cdb",
        "nome": "CDB do Banco do Brasil",
        "instituicao": "Banco do Brasil",
        "valor_aplicado": "5000.00",
        "aplicado_em": "2026-03-10",
        "vence_em": "2028-03-10",
        "indexador": "cdi",
        "taxa": "110.00",
        "liquidez_diaria": False,
    }
    assert corpo["id"] and corpo["criado_em"]


def test_renda_fixa_prefixada_so_com_o_obrigatorio(cliente_logado: TestClient) -> None:
    resposta = cliente_logado.post(
        "/api/v1/investimentos",
        json={
            "tipo": "renda_fixa",
            "nome": "  Tesouro Prefixado  ",
            "valor_aplicado": "1000",
            "aplicado_em": HOJE.isoformat(),
            "indexador": "prefixado",
            "taxa": "12.5",
        },
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nome"] == "Tesouro Prefixado"
    assert corpo["instituicao"] is None
    assert corpo["vence_em"] is None
    assert corpo["taxa"] == "12.50"
    assert corpo["liquidez_diaria"] is False


def test_lista_do_mais_recente_para_o_mais_antigo(cliente_logado: TestClient) -> None:
    cliente_logado.post("/api/v1/investimentos", json=_cdb(nome="Antigo"))
    cliente_logado.post(
        "/api/v1/investimentos",
        json=_cdb(nome="Novo", aplicado_em="2026-09-01", vence_em=None),
    )

    nomes = [i["nome"] for i in cliente_logado.get("/api/v1/investimentos").json()]

    assert nomes == ["Novo", "Antigo"]


def test_nao_mostra_investimento_de_outra_pessoa(
    sessao: Session, cliente: TestClient, cliente_logado: TestClient
) -> None:
    cliente_logado.post("/api/v1/investimentos", json=_cdb())
    outro = Usuario(
        id=uuid.uuid4(),
        nome="José",
        hash_telefone=uuid.uuid4().hex,
        email=f"jose{uuid.uuid4().hex[:8]}@vero.com",
        hash_pin="x",
        tentativas=0,
    )
    sessao.add(outro)
    sessao.flush()
    token = criar_token(outro.id, "pin", timedelta(hours=1))

    resposta = cliente.get(
        "/api/v1/investimentos", headers={"Authorization": f"Bearer {token}"}
    )

    assert resposta.json() == []


@pytest.mark.parametrize(
    ("campo", "valor", "mensagem"),
    [
        ("valor_aplicado", "0", Message.VALOR_INVALIDO.message),
        ("valor_aplicado", "-10", Message.VALOR_INVALIDO.message),
        ("valor_aplicado", "10000000000", Message.VALOR_MUITO_ALTO.message),
        ("nome", "   ", Message.NOME_EM_BRANCO.message),
        (
            "aplicado_em",
            (HOJE + timedelta(days=1)).isoformat(),
            Message.APLICACAO_NO_FUTURO.message,
        ),
        ("vence_em", "2026-03-10", Message.VENCIMENTO_ANTES_DA_APLICACAO.message),
        ("vence_em", "2025-01-01", Message.VENCIMENTO_ANTES_DA_APLICACAO.message),
        (
            "taxa",
            "0",
            Message.PERCENTUAL_CDI_FORA_DO_LIMITE.message.format(maximo=300),
        ),
        (
            "taxa",
            "301",
            Message.PERCENTUAL_CDI_FORA_DO_LIMITE.message.format(maximo=300),
        ),
    ],
)
def test_dado_que_nao_esta_certo_aponta_o_campo_e_explica(
    cliente_logado: TestClient, campo: str, valor: str, mensagem: str
) -> None:
    resposta = cliente_logado.post("/api/v1/investimentos", json=_cdb(**{campo: valor}))

    assert _erros(resposta) == [{"campo": campo, "mensagem": mensagem}]


def test_taxa_prefixada_vai_ate_100_por_cento_ao_ano(
    cliente_logado: TestClient,
) -> None:
    acima = cliente_logado.post(
        "/api/v1/investimentos", json=_cdb(indexador="prefixado", taxa="101")
    )
    no_limite = cliente_logado.post(
        "/api/v1/investimentos", json=_cdb(indexador="prefixado", taxa="100")
    )

    assert _erros(acima) == [
        {
            "campo": "taxa",
            "mensagem": Message.TAXA_PREFIXADA_FORA_DO_LIMITE.message.format(
                maximo=100
            ),
        }
    ]
    assert no_limite.status_code == 201


def test_cdi_vai_ate_300_por_cento(cliente_logado: TestClient) -> None:
    resposta = cliente_logado.post("/api/v1/investimentos", json=_cdb(taxa="300"))

    assert resposta.status_code == 201


@pytest.mark.parametrize(("campo", "valor"), [("tipo", "acoes"), ("indexador", "ipca")])
def test_tipo_e_indexador_so_aceitam_os_valores_previstos(
    cliente_logado: TestClient, campo: str, valor: str
) -> None:
    resposta = cliente_logado.post("/api/v1/investimentos", json=_cdb(**{campo: valor}))

    assert [e["campo"] for e in _erros(resposta)] == [campo]


def test_sem_entrar_na_conta_retorna_401(cliente: TestClient) -> None:
    assert cliente.get("/api/v1/investimentos").status_code == 401
    assert cliente.post("/api/v1/investimentos", json=_cdb()).status_code == 401
