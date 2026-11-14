"""Testes do histórico de transações: listar, editar e excluir (RF10)."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modulos.identidade.modelos import Usuario
from app.modulos.transacoes.modelos import Transacao


def _transacao(
    sessao: Session,
    usuario_id: uuid.UUID,
    data: date = date(2026, 3, 10),
    valor: str = "50.00",
) -> Transacao:
    transacao = Transacao(
        usuario_id=usuario_id,
        tipo="saida",
        valor=Decimal(valor),
        data=data,
        descricao="Mercado",
        origem="manual",
    )
    sessao.add(transacao)
    sessao.flush()
    return transacao


def _outro_usuario(sessao: Session) -> Usuario:
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
    return outro


def test_historico_lista_do_mais_recente_para_o_mais_antigo(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    _transacao(sessao, usuario.id, date(2026, 3, 1))
    _transacao(sessao, usuario.id, date(2026, 3, 20))

    datas = [t["data"] for t in cliente_logado.get("/api/v1/transacoes").json()]

    assert datas == ["2026-03-20", "2026-03-01"]


def test_historico_nao_mostra_transacao_de_outro_usuario(
    sessao: Session, cliente_logado: TestClient
) -> None:
    _transacao(sessao, _outro_usuario(sessao).id)

    assert cliente_logado.get("/api/v1/transacoes").json() == []


def test_edita_valor_categoria_e_data(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    transacao = _transacao(sessao, usuario.id)

    resposta = cliente_logado.patch(
        f"/api/v1/transacoes/{transacao.id}",
        json={"valor": "75.50", "data": "2026-03-12", "categoria_id": None},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["valor"] == "75.50"
    assert corpo["data"] == "2026-03-12"
    assert corpo["descricao"] == "Mercado"  # campo não enviado fica igual


def test_edicao_nao_aceita_valor_em_branco(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    transacao = _transacao(sessao, usuario.id)

    resposta = cliente_logado.patch(
        f"/api/v1/transacoes/{transacao.id}", json={"valor": None}
    )

    assert resposta.status_code == 422
    assert "não podem ficar em branco" in resposta.text


def test_edicao_nao_aceita_valor_zero(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    transacao = _transacao(sessao, usuario.id)

    resposta = cliente_logado.patch(
        f"/api/v1/transacoes/{transacao.id}", json={"valor": "0"}
    )

    assert resposta.status_code == 422


def test_edicao_com_categoria_inexistente_retorna_422(
    sessao: Session,
    usuario: Usuario,
    cliente_logado: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transacao = _transacao(sessao, usuario.id)

    def commit_com_fk_invalida() -> None:
        raise IntegrityError("UPDATE tblTransacao", {}, Exception("fk"))

    # O banco de teste é criado pelo metadata, sem a FK de categoria da migration
    monkeypatch.setattr(sessao, "commit", commit_com_fk_invalida)

    resposta = cliente_logado.patch(
        f"/api/v1/transacoes/{transacao.id}", json={"categoria_id": 999}
    )

    assert resposta.status_code == 422
    assert "categoria não existe" in resposta.text


def test_nao_edita_transacao_de_outro_usuario(
    sessao: Session, cliente_logado: TestClient
) -> None:
    transacao = _transacao(sessao, _outro_usuario(sessao).id)

    resposta = cliente_logado.patch(
        f"/api/v1/transacoes/{transacao.id}", json={"valor": "1.00"}
    )

    assert resposta.status_code == 404
    assert transacao.valor == Decimal("50.00")


def test_exclui_transacao(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    transacao = _transacao(sessao, usuario.id)

    resposta = cliente_logado.delete(f"/api/v1/transacoes/{transacao.id}")

    assert resposta.status_code == 204
    assert cliente_logado.get("/api/v1/transacoes").json() == []


def test_nao_exclui_transacao_de_outro_usuario(
    sessao: Session, cliente_logado: TestClient
) -> None:
    transacao = _transacao(sessao, _outro_usuario(sessao).id)

    resposta = cliente_logado.delete(f"/api/v1/transacoes/{transacao.id}")

    assert resposta.status_code == 404
    assert sessao.get(Transacao, transacao.id) is not None


def test_historico_sem_autenticacao_retorna_401(cliente: TestClient) -> None:
    assert cliente.get("/api/v1/transacoes").status_code == 401
