"""Testes do cadastro e login com PIN (RF01 - identidade)."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.seguranca import gerar_hash


class TestCadastro:
    """POST /api/v1/auth/cadastro"""

    def test_cadastro_com_telefone_pin_e_email_retorna_201(
        self, cliente: TestClient
    ) -> None:
        resp = cliente.post(
            "/api/v1/auth/cadastro",
            json={
                "nome": "João",
                "telefone": "5561999998888",
                "email": "joao@vero.com",
                "pin": "123456",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["nome"] == "João"
        assert body["telefone"] == "5561999998888"
        assert body["email"] == "joao@vero.com"
        assert body["tem_pin"] is True

    def test_cadastro_sem_email_retorna_422(self, cliente: TestClient) -> None:
        resp = cliente.post(
            "/api/v1/auth/cadastro",
            json={
                "nome": "Maria",
                "telefone": "5561988887777",
                "pin": "1234",
            },
        )
        assert resp.status_code == 422

    def test_cadastro_telefone_duplicado_retorna_409(self, cliente: TestClient) -> None:
        telefone = "5561977776666"
        cliente.post(
            "/api/v1/auth/cadastro",
            json={
                "nome": "A",
                "telefone": telefone,
                "email": "a@vero.com",
                "pin": "1111",
            },
        )
        resp = cliente.post(
            "/api/v1/auth/cadastro",
            json={
                "nome": "B",
                "telefone": telefone,
                "email": "b@vero.com",
                "pin": "2222",
            },
        )
        assert resp.status_code == 409
        assert "celular" in resp.text.lower()

    def test_cadastro_email_duplicado_retorna_409(self, cliente: TestClient) -> None:
        email = "dup@vero.com"
        cliente.post(
            "/api/v1/auth/cadastro",
            json={
                "nome": "A",
                "telefone": "5561955554444",
                "email": email,
                "pin": "1111",
            },
        )
        resp = cliente.post(
            "/api/v1/auth/cadastro",
            json={
                "nome": "B",
                "telefone": "5561955553333",
                "email": email,
                "pin": "2222",
            },
        )
        assert resp.status_code == 409
        assert "e-mail" in resp.text.lower()

    def test_cadastro_pin_curto_retorna_422(self, cliente: TestClient) -> None:
        resp = cliente.post(
            "/api/v1/auth/cadastro",
            json={"nome": "X", "telefone": "5561944443333", "pin": "123"},
        )
        assert resp.status_code == 422

    def test_cadastro_pin_longo_retorna_422(self, cliente: TestClient) -> None:
        resp = cliente.post(
            "/api/v1/auth/cadastro",
            json={"nome": "X", "telefone": "5561944442222", "pin": "1234567"},
        )
        assert resp.status_code == 422

    def test_cadastro_sem_nome_retorna_422(self, cliente: TestClient) -> None:
        resp = cliente.post(
            "/api/v1/auth/cadastro",
            json={"telefone": "5561933332222", "pin": "1234"},
        )
        assert resp.status_code == 422

    def test_cadastro_sem_telefone_retorna_422(self, cliente: TestClient) -> None:
        resp = cliente.post(
            "/api/v1/auth/cadastro",
            json={"nome": "X", "pin": "1234"},
        )
        assert resp.status_code == 422

    def test_cadastro_sem_pin_retorna_422(self, cliente: TestClient) -> None:
        resp = cliente.post(
            "/api/v1/auth/cadastro",
            json={"nome": "X", "telefone": "5561922221111"},
        )
        assert resp.status_code == 422


class TestLoginPin:
    """POST /api/v1/auth/login (apenas PIN)"""

    @pytest.fixture
    def usuario_com_pin(self, sessao: Session) -> Usuario:
        u = Usuario(
            id=uuid.uuid4(),
            nome="Teste",
            telefone="5561911110000",
            email="teste@vero.com",
            hash_pin=gerar_hash("123456"),
        )
        sessao.add(u)
        sessao.flush()
        sessao.refresh(u)
        return u

    def test_login_com_pin_correto_retorna_token(
        self, cliente: TestClient, usuario_com_pin: Usuario
    ) -> None:
        resp = cliente.post(
            "/api/v1/auth/login",
            json={"telefone": "5561911110000", "pin": "123456"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["expira_em"] == 7200  # 2 horas em segundos

    def test_login_com_pin_errado_retorna_401(
        self, cliente: TestClient, usuario_com_pin: Usuario
    ) -> None:
        resp = cliente.post(
            "/api/v1/auth/login",
            json={"telefone": "5561911110000", "pin": "654321"},
        )
        assert resp.status_code == 401
        assert "pin" in resp.text.lower()

    def test_login_usuario_inexistente_retorna_401(self, cliente: TestClient) -> None:
        resp = cliente.post(
            "/api/v1/auth/login",
            json={"telefone": "5561900000000", "pin": "123456"},
        )
        assert resp.status_code == 401

    def test_login_bloqueia_apos_5_tentativas_erradas(
        self, cliente: TestClient, usuario_com_pin: Usuario
    ) -> None:
        # 4 tentativas erradas -> 401
        for _ in range(4):
            resp = cliente.post(
                "/api/v1/auth/login",
                json={"telefone": "5561911110000", "pin": "errado"},
            )
            assert resp.status_code == 401

        # 5ª tentativa -> bloqueia (429)
        resp = cliente.post(
            "/api/v1/auth/login",
            json={"telefone": "5561911110000", "pin": "errado"},
        )
        assert resp.status_code == 429
        assert "tentativas" in resp.text.lower()
        assert "Retry-After" in resp.headers


class TestLoginAntigoRemovido:
    """Garante que endpoints de senha foram removidos"""

    def test_nao_existe_endpoint_login_senha(self, cliente: TestClient) -> None:
        resp = cliente.post(
            "/api/v1/auth/login",
            json={"telefone": "5561999998888", "senha": "qualquer"},
        )
        # deve falhar porque o schema espera 'pin', não 'senha'
        assert resp.status_code == 422

    def test_rota_antiga_pin_funciona_como_login(self, cliente: TestClient) -> None:
        # voltando com /pin em vez de /login
        resp = cliente.post(
            "/api/v1/auth/pin",
            json={"telefone": "5561911110000", "pin": "123456"},
        )
        # Usuário não existe -> 401 (credenciais inválidas), não 404
        assert resp.status_code == 401


class TestUsuarioSaida:
    """Valida schema de resposta UsuarioSaida"""

    def test_resposta_inclui_email_obrigatorio(self, cliente: TestClient) -> None:
        resp = cliente.post(
            "/api/v1/auth/cadastro",
            json={
                "nome": "Com Email",
                "telefone": "5561900001111",
                "email": "teste@vero.com",
                "pin": "1234",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["email"] == "teste@vero.com"

    def test_resposta_inclui_tem_pin_true(self, cliente: TestClient) -> None:
        resp = cliente.post(
            "/api/v1/auth/cadastro",
            json={
                "nome": "Com Pin",
                "telefone": "5561900002222",
                "email": "pin@vero.com",
                "pin": "123456",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["tem_pin"] is True
