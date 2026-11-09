"""Testes do cadastro de contas (RF25)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modulos.contas.modelos import Conta


def test_cadastro_com_data_e_valor_retorna_201_e_status_a_vencer(
    cliente_logado: TestClient,
) -> None:
    vencimento = date.today() + timedelta(days=10)
    resposta = cliente_logado.post(
        "/api/v1/contas",
        json={"vencimento_em": vencimento.isoformat(), "valor": "150.00"},
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "a_vencer"
    assert corpo["valor"] == "150.00"
    assert corpo["descricao"] is None
    assert corpo["categoria_id"] is None


def test_cadastro_aceita_descricao_e_categoria_opcionais(
    cliente_logado: TestClient,
) -> None:
    vencimento = date.today() + timedelta(days=5)
    resposta = cliente_logado.post(
        "/api/v1/contas",
        json={
            "vencimento_em": vencimento.isoformat(),
            "valor": "89.90",
            "descricao": "Conta de luz",
        },
    )

    assert resposta.status_code == 201
    assert resposta.json()["descricao"] == "Conta de luz"


def test_cadastro_com_valor_zero_retorna_422(cliente_logado: TestClient) -> None:
    resposta = cliente_logado.post(
        "/api/v1/contas",
        json={"vencimento_em": date.today().isoformat(), "valor": "0"},
    )

    assert resposta.status_code == 422
    assert "maior que zero" in resposta.text


def test_cadastro_com_valor_negativo_retorna_422(cliente_logado: TestClient) -> None:
    resposta = cliente_logado.post(
        "/api/v1/contas",
        json={"vencimento_em": date.today().isoformat(), "valor": "-10.00"},
    )

    assert resposta.status_code == 422


def test_cadastro_sem_data_retorna_422(cliente_logado: TestClient) -> None:
    resposta = cliente_logado.post("/api/v1/contas", json={"valor": "50.00"})

    assert resposta.status_code == 422


def test_conta_vencida_fica_em_atraso(cliente_logado: TestClient) -> None:
    ontem = date.today() - timedelta(days=1)
    resposta = cliente_logado.post(
        "/api/v1/contas",
        json={"vencimento_em": ontem.isoformat(), "valor": "20.00"},
    )

    assert resposta.status_code == 201
    assert resposta.json()["status"] == "em_atraso"


def test_cadastro_sem_autenticacao_retorna_401(cliente: TestClient) -> None:
    resposta = cliente.post(
        "/api/v1/contas",
        json={"vencimento_em": date.today().isoformat(), "valor": "10.00"},
    )

    assert resposta.status_code == 401


def test_listagem_ordena_por_vencimento(cliente_logado: TestClient) -> None:
    for dias in (20, 5, 10):
        cliente_logado.post(
            "/api/v1/contas",
            json={
                "vencimento_em": (date.today() + timedelta(days=dias)).isoformat(),
                "valor": "10.00",
            },
        )

    contas = cliente_logado.get("/api/v1/contas").json()
    vencimentos = [c["vencimento_em"] for c in contas]
    assert vencimentos == sorted(vencimentos)


def test_cadastro_com_valor_acima_do_maximo_retorna_422(
    cliente_logado: TestClient,
) -> None:
    resposta = cliente_logado.post(
        "/api/v1/contas",
        json={"vencimento_em": date.today().isoformat(), "valor": "10000000000.00"},
    )

    assert resposta.status_code == 422
    assert "muito alto" in resposta.text


def test_str_da_conta_usa_descricao_ou_conta() -> None:
    assert str(Conta(descricao="Conta de luz", valor=Decimal("10.00"))) == (
        "Conta de luz — 10.00"
    )
    assert str(Conta(descricao=None, valor=Decimal("10.00"))) == "Conta — 10.00"


def test_cadastro_com_categoria_inexistente_retorna_422(
    cliente_logado: TestClient,
    sessao: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def commit_com_fk_invalida() -> None:
        raise IntegrityError("INSERT INTO tblConta", {}, Exception("fk"))

    # O banco de teste é criado pelo metadata, sem a FK de categoria da migration.
    # Simulamos a violação para cobrir o tratamento da categoria inexistente.
    monkeypatch.setattr(sessao, "commit", commit_com_fk_invalida)

    resposta = cliente_logado.post(
        "/api/v1/contas",
        json={
            "vencimento_em": date.today().isoformat(),
            "valor": "10.00",
            "categoria_id": 999,
        },
    )

    assert resposta.status_code == 422
    assert "categoria não existe" in resposta.text
