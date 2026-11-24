"""#133: apagar conta de verdade (antes a tela dizia "apagada" e a API dava 404)."""

import uuid
from datetime import date, timedelta

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.modulos.contas.mensagens import Message
from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.seguranca import criar_token
from app.nucleo import eventos


@pytest.fixture(autouse=True)
def preparar(fixar_hoje_contas, monkeypatch) -> None:
    fixar_hoje_contas(date(2026, 11, 14))
    monkeypatch.setattr(eventos, "cliente", fakeredis.FakeRedis())


def _cadastrar(cliente: TestClient, **extra) -> dict:
    dados = {"vencimento_em": "2026-11-20", "valor": "120.00", "descricao": "Luz"}
    resposta = cliente.post("/api/v1/contas", json=dados | extra)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def _ids(cliente: TestClient) -> list[str]:
    return [c["id"] for c in cliente.get("/api/v1/contas").json()]


def test_apaga_a_conta(cliente_logado: TestClient) -> None:
    conta = _cadastrar(cliente_logado)

    resposta = cliente_logado.delete(f"/api/v1/contas/{conta['id']}")

    assert resposta.status_code == 204
    assert conta["id"] not in _ids(cliente_logado)


def test_conta_inexistente_ou_de_outra_pessoa_da_404(
    cliente_logado: TestClient, sessao
) -> None:
    outra = Usuario(
        id=uuid.uuid4(),
        nome="Outra",
        hash_telefone=uuid.uuid4().hex,
        email=f"o{uuid.uuid4().hex[:8]}@vero.com",
        hash_pin="x",
        tentativas=0,
    )
    sessao.add(outra)
    sessao.flush()
    conta = _cadastrar(cliente_logado)
    token_outra = criar_token(outra.id, "pin", timedelta(hours=1))

    resposta = cliente_logado.delete(
        f"/api/v1/contas/{conta['id']}",
        headers={"Authorization": f"Bearer {token_outra}"},
    )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == Message.CONTA_NAO_ENCONTRADA.message
    assert cliente_logado.delete(f"/api/v1/contas/{uuid.uuid4()}").status_code == 404


def test_apagar_a_primeira_parcela_mantem_as_outras(cliente_logado: TestClient) -> None:
    primeira = _cadastrar(
        cliente_logado, vencimento_em="2026-11-14", valor="900.00", parcelas=3
    )

    assert cliente_logado.delete(f"/api/v1/contas/{primeira['id']}").status_code == 204

    restantes = cliente_logado.get("/api/v1/contas").json()
    assert [c["parcela"] for c in restantes] == [2, 3]
    assert all(c["id_conta_origem"] is None for c in restantes)


def test_conta_ja_lancada_no_extrato_da_409(
    cliente_logado: TestClient, monkeypatch
) -> None:
    """No banco migrado, a FK da tblTransacao.idConta barra a exclusão."""
    conta = _cadastrar(cliente_logado)

    def commit_com_fk(self):
        raise IntegrityError("DELETE", {}, Exception("fk tblTransacao.idConta"))

    monkeypatch.setattr("sqlalchemy.orm.Session.commit", commit_com_fk)
    resposta = cliente_logado.delete(f"/api/v1/contas/{conta['id']}")

    assert resposta.status_code == 409
    assert "apague o gasto no Extrato primeiro" in resposta.json()["detail"]
