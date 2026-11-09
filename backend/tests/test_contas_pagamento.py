"""Testes de marcar e desfazer o pagamento de contas (RF30)."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modulos.contas.modelos import Conta
from app.modulos.contas.saldo import ESTRATEGIA_SALDO, SaldoInalterado
from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.seguranca import gerar_hash


def _cadastrar_conta(
    cliente: TestClient,
    dias: int = 10,
    descricao: str | None = None,
) -> dict:
    dados = {
        "vencimento_em": (date.today() + timedelta(days=dias)).isoformat(),
        "valor": "150.00",
    }
    if descricao is not None:
        dados["descricao"] = descricao

    resposta = cliente.post("/api/v1/contas", json=dados)
    assert resposta.status_code == 201
    return resposta.json()


def _criar_outro_usuario(sessao: Session) -> Usuario:
    sufixo = uuid.uuid4().hex[:8]
    usuario = Usuario(
        nome="João",
        telefone="55619" + sufixo,
        email=f"joao{sufixo}@vero.com",
        hash_senha=gerar_hash("senha12345"),
        tentativas=0,
    )
    sessao.add(usuario)
    sessao.commit()
    sessao.refresh(usuario)
    return usuario


def _pagar(cliente: TestClient, conta_id: str, paga: bool = True):
    return cliente.patch(
        f"/api/v1/contas/{conta_id}/pagamento",
        json={"paga": paga},
    )


def test_marcar_conta_como_paga_retorna_status_e_data(
    cliente_logado: TestClient,
) -> None:
    conta = _cadastrar_conta(cliente_logado, descricao="Conta de luz")

    resposta = _pagar(cliente_logado, conta["id"])

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "paga"
    assert corpo["pagamento_em"] is not None
    assert corpo["valor"] == conta["valor"]
    assert corpo["vencimento_em"] == conta["vencimento_em"]
    assert corpo["descricao"] == "Conta de luz"
    assert corpo["categoria_id"] is None


def test_marcar_paga_duas_vezes_e_idempotente(cliente_logado: TestClient) -> None:
    conta = _cadastrar_conta(cliente_logado)

    primeira = _pagar(cliente_logado, conta["id"])
    segunda = _pagar(cliente_logado, conta["id"])

    assert primeira.status_code == 200
    assert segunda.status_code == 200
    assert segunda.json()["status"] == "paga"
    assert segunda.json()["pagamento_em"] == primeira.json()["pagamento_em"]


def test_desfazer_pagamento_volta_conta_futura_para_a_vencer(
    cliente_logado: TestClient,
) -> None:
    conta = _cadastrar_conta(cliente_logado, dias=10)
    _pagar(cliente_logado, conta["id"])

    resposta = _pagar(cliente_logado, conta["id"], paga=False)

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "a_vencer"
    assert resposta.json()["pagamento_em"] is None


def test_desfazer_pagamento_volta_conta_vencida_para_em_atraso(
    cliente_logado: TestClient,
) -> None:
    conta = _cadastrar_conta(cliente_logado, dias=-1)
    assert conta["status"] == "em_atraso"
    _pagar(cliente_logado, conta["id"])

    resposta = _pagar(cliente_logado, conta["id"], paga=False)

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "em_atraso"
    assert resposta.json()["pagamento_em"] is None


def test_desfazer_duas_vezes_e_idempotente(cliente_logado: TestClient) -> None:
    conta = _cadastrar_conta(cliente_logado)

    primeira = _pagar(cliente_logado, conta["id"], paga=False)
    segunda = _pagar(cliente_logado, conta["id"], paga=False)

    assert primeira.status_code == 200
    assert segunda.status_code == 200
    assert segunda.json()["status"] == "a_vencer"
    assert segunda.json()["pagamento_em"] is None


def test_nao_altera_conta_de_outro_usuario(
    cliente_logado: TestClient, sessao: Session
) -> None:
    outro = _criar_outro_usuario(sessao)
    conta = Conta(
        usuario_id=outro.id,
        vencimento_em=date.today() + timedelta(days=5),
        valor=Decimal("30.00"),
    )
    sessao.add(conta)
    sessao.commit()
    sessao.refresh(conta)

    resposta = _pagar(cliente_logado, str(conta.id))

    assert resposta.status_code == 404
    assert "Não encontramos essa conta" in resposta.text
    sessao.refresh(conta)
    assert conta.pagamento_em is None


def test_conta_inexistente_retorna_404(cliente_logado: TestClient) -> None:
    resposta = _pagar(cliente_logado, str(uuid.uuid4()))

    assert resposta.status_code == 404


def test_pagamento_sem_autenticacao_retorna_401(cliente: TestClient) -> None:
    resposta = cliente.patch(
        f"/api/v1/contas/{uuid.uuid4()}/pagamento",
        json={"paga": True},
    )

    assert resposta.status_code == 401


def test_estrategia_padrao_nao_desconta_do_saldo() -> None:
    assert isinstance(ESTRATEGIA_SALDO, SaldoInalterado)
