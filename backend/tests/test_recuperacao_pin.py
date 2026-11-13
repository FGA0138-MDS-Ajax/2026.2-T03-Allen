"""Testes do "esqueci meu PIN", da troca de PIN e da versão do token (RF01, critério 5)."""

import asyncio
import re
import uuid
from contextlib import nullcontext
from datetime import UTC, datetime, timedelta

import fakeredis
import jwt
import pytest
import valkey
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect

from app.integracoes.correio import obter_email
from app.main import app
from app.modulos.identidade import recuperacao
from app.modulos.identidade.mensagens import Message
from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.seguranca import criar_token, gerar_hash, hash_telefone
from app.modulos.identidade.servico import Attempts
from app.modulos.tempo_real import router as router_tempo_real
from app.nucleo import eventos
from app.nucleo.config import settings

PIN_ATUAL = "123456"
NOVO_PIN = "4321"

ESQUECI = "/api/v1/auth/pin/esqueci"
REDEFINIR = "/api/v1/auth/pin/redefinir"
TROCAR = "/api/v1/auth/pin"
LOGIN = "/api/v1/auth/login"
ROTA_PROTEGIDA = "/api/v1/contas"


class EmailCapturado:
    """Adaptador de e-mail dos testes: guarda as mensagens em vez de enviar."""

    def __init__(self) -> None:
        self.enviados: list[dict] = []

    def enviar(self, destinatario: str, assunto: str, texto: str) -> None:
        self.enviados.append(
            {"destinatario": destinatario, "assunto": assunto, "texto": texto}
        )

    def ultimo_codigo(self) -> str:
        return re.search(r"\b(\d{6})\b", self.enviados[-1]["texto"]).group(1)


class ValkeyFora:
    """Simula o Valkey sem responder."""

    def __getattr__(self, _nome):
        def falhar(*_args, **_kwargs):
            raise valkey.ConnectionError("Valkey fora do ar")

        return falhar


@pytest.fixture(autouse=True)
def valkey_falso(monkeypatch: pytest.MonkeyPatch) -> fakeredis.FakeRedis:
    falso = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(recuperacao, "cliente", falso)
    return falso


@pytest.fixture
def correio() -> EmailCapturado:
    capturado = EmailCapturado()
    app.dependency_overrides[obter_email] = lambda: capturado
    yield capturado
    app.dependency_overrides.pop(obter_email, None)


@pytest.fixture
def titular(sessao: Session) -> Usuario:
    """Usuário com celular só de dígitos, que passa na validação da API."""
    telefone = "55619" + str(uuid.uuid4().int)[:8]
    u = Usuario(
        id=uuid.uuid4(),
        nome="Maria",
        hash_telefone=hash_telefone(telefone),
        email=f"maria{uuid.uuid4().hex[:8]}@gmail.com",
        hash_pin=gerar_hash(PIN_ATUAL),
        tentativas=0,
    )
    u.telefone = telefone
    sessao.add(u)
    sessao.commit()
    return u


def _pedir_codigo(cliente: TestClient, usuario: Usuario):
    return cliente.post(ESQUECI, json={"telefone": usuario.telefone})


def _liberar_reenvio(falso: fakeredis.FakeRedis, usuario: Usuario) -> None:
    """Pula a espera de 60 s entre pedidos."""
    falso.delete(f"vero:recuperacao:espera:{usuario.id}")


def _redefinir(cliente: TestClient, usuario: Usuario, codigo: str, pin=NOVO_PIN):
    return cliente.post(
        REDEFINIR,
        json={"telefone": usuario.telefone, "codigo": codigo, "novo_pin": pin},
    )


def _login(cliente: TestClient, usuario: Usuario, pin: str):
    return cliente.post(LOGIN, json={"telefone": usuario.telefone, "pin": pin})


def _codigo_errado(codigo: str) -> str:
    return f"{(int(codigo) + 1) % 10**6:06d}"


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestEsqueciPin:
    """POST /api/v1/auth/pin/esqueci"""

    def test_envia_codigo_para_email_do_cadastro(
        self, cliente: TestClient, titular: Usuario, correio: EmailCapturado
    ) -> None:
        resp = _pedir_codigo(cliente, titular)

        assert resp.status_code == 202
        corpo = resp.json()
        assert corpo["enviado_para"] == f"m***@{titular.email.split('@')[1]}"
        assert corpo["validade_minutos"] == 15
        assert len(correio.enviados) == 1
        assert correio.enviados[0]["destinatario"] == titular.email
        assert re.fullmatch(r"\d{6}", correio.ultimo_codigo())

    def test_codigo_fica_no_valkey_so_como_hash_e_com_validade(
        self,
        cliente: TestClient,
        titular: Usuario,
        correio: EmailCapturado,
        valkey_falso: fakeredis.FakeRedis,
    ) -> None:
        _pedir_codigo(cliente, titular)

        chave = f"vero:recuperacao:codigo:{titular.id}"
        salvo = valkey_falso.hgetall(chave)
        assert correio.ultimo_codigo() not in salvo.values()
        assert salvo["hash"] != correio.ultimo_codigo()
        assert 0 < valkey_falso.ttl(chave) <= 15 * 60

    def test_celular_sem_conta_retorna_404(
        self, cliente: TestClient, correio: EmailCapturado
    ) -> None:
        resp = cliente.post(ESQUECI, json={"telefone": "5561900000000"})

        assert resp.status_code == 404
        assert resp.json()["detail"] == Message.CELULAR_SEM_CONTA.message
        assert correio.enviados == []

    def test_celular_invalido_retorna_422(self, cliente: TestClient) -> None:
        resp = cliente.post(ESQUECI, json={"telefone": "123"})
        assert resp.status_code == 422

    def test_novo_pedido_antes_de_60s_retorna_429(
        self, cliente: TestClient, titular: Usuario, correio: EmailCapturado
    ) -> None:
        _pedir_codigo(cliente, titular)
        resp = _pedir_codigo(cliente, titular)

        assert resp.status_code == 429
        assert 0 < int(resp.headers["Retry-After"]) <= 60
        assert len(correio.enviados) == 1

    def test_sexto_pedido_na_mesma_hora_retorna_429(
        self,
        cliente: TestClient,
        titular: Usuario,
        correio: EmailCapturado,
        valkey_falso: fakeredis.FakeRedis,
    ) -> None:
        for _ in range(5):
            assert _pedir_codigo(cliente, titular).status_code == 202
            _liberar_reenvio(valkey_falso, titular)

        resp = _pedir_codigo(cliente, titular)

        assert resp.status_code == 429
        assert resp.json()["detail"] == Message.MUITOS_CODIGOS.message
        assert len(correio.enviados) == 5

    def test_valkey_fora_do_ar_retorna_503(
        self,
        cliente: TestClient,
        titular: Usuario,
        correio: EmailCapturado,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(recuperacao, "cliente", ValkeyFora())

        resp = _pedir_codigo(cliente, titular)

        assert resp.status_code == 503
        assert correio.enviados == []


class TestRedefinirPin:
    """POST /api/v1/auth/pin/redefinir"""

    def test_codigo_certo_grava_novo_pin_e_devolve_token(
        self, cliente: TestClient, titular: Usuario, correio: EmailCapturado
    ) -> None:
        _pedir_codigo(cliente, titular)

        resp = _redefinir(cliente, titular, correio.ultimo_codigo())

        assert resp.status_code == 200
        token = resp.json()["access_token"]
        assert cliente.get(ROTA_PROTEGIDA, headers=_bearer(token)).status_code == 200
        assert _login(cliente, titular, NOVO_PIN).status_code == 200
        assert _login(cliente, titular, PIN_ATUAL).status_code == 401

    def test_codigo_errado_retorna_400(
        self, cliente: TestClient, titular: Usuario, correio: EmailCapturado
    ) -> None:
        _pedir_codigo(cliente, titular)

        resp = _redefinir(cliente, titular, _codigo_errado(correio.ultimo_codigo()))

        assert resp.status_code == 400
        assert resp.json()["detail"] == Message.CODIGO_ERRADO.message
        assert _login(cliente, titular, PIN_ATUAL).status_code == 200

    def test_codigo_so_vale_uma_vez(
        self, cliente: TestClient, titular: Usuario, correio: EmailCapturado
    ) -> None:
        _pedir_codigo(cliente, titular)
        codigo = correio.ultimo_codigo()

        assert _redefinir(cliente, titular, codigo).status_code == 200
        assert _redefinir(cliente, titular, codigo, pin="9999").status_code == 400
        assert _login(cliente, titular, NOVO_PIN).status_code == 200

    def test_codigo_deixa_de_valer_apos_5_erros(
        self, cliente: TestClient, titular: Usuario, correio: EmailCapturado
    ) -> None:
        _pedir_codigo(cliente, titular)
        codigo = correio.ultimo_codigo()
        for _ in range(5):
            assert (
                _redefinir(cliente, titular, _codigo_errado(codigo)).status_code == 400
            )

        assert _redefinir(cliente, titular, codigo).status_code == 400

    def test_quarto_erro_ainda_deixa_usar_o_codigo_certo(
        self, cliente: TestClient, titular: Usuario, correio: EmailCapturado
    ) -> None:
        _pedir_codigo(cliente, titular)
        codigo = correio.ultimo_codigo()
        for _ in range(4):
            _redefinir(cliente, titular, _codigo_errado(codigo))

        assert _redefinir(cliente, titular, codigo).status_code == 200

    def test_codigo_vencido_retorna_400(
        self,
        cliente: TestClient,
        titular: Usuario,
        correio: EmailCapturado,
        valkey_falso: fakeredis.FakeRedis,
    ) -> None:
        _pedir_codigo(cliente, titular)
        chave = f"vero:recuperacao:codigo:{titular.id}"
        valkey_falso.delete(chave)  # o Valkey apaga a chave quando a validade acaba

        resp = _redefinir(cliente, titular, correio.ultimo_codigo())

        assert resp.status_code == 400
        # A tentativa não deixa uma chave sem validade para trás
        assert not valkey_falso.exists(chave)

    def test_novo_pedido_invalida_codigo_anterior(
        self,
        cliente: TestClient,
        titular: Usuario,
        correio: EmailCapturado,
        valkey_falso: fakeredis.FakeRedis,
    ) -> None:
        _pedir_codigo(cliente, titular)
        primeiro = correio.ultimo_codigo()
        _liberar_reenvio(valkey_falso, titular)
        _pedir_codigo(cliente, titular)
        segundo = correio.ultimo_codigo()
        if primeiro == segundo:
            pytest.skip("os dois códigos sorteados foram iguais")

        assert _redefinir(cliente, titular, primeiro).status_code == 400
        assert _redefinir(cliente, titular, segundo).status_code == 200

    def test_celular_sem_conta_retorna_400(self, cliente: TestClient) -> None:
        resp = cliente.post(
            REDEFINIR,
            json={"telefone": "5561900000000", "codigo": "123456", "novo_pin": "1111"},
        )
        assert resp.status_code == 400

    @pytest.mark.parametrize("codigo", ["12345", "1234567", "abcdef"])
    def test_codigo_fora_do_formato_retorna_422(
        self, cliente: TestClient, titular: Usuario, codigo: str
    ) -> None:
        assert _redefinir(cliente, titular, codigo).status_code == 422

    @pytest.mark.parametrize("pin", ["123", "1234567", "12ab"])
    def test_novo_pin_invalido_retorna_422(
        self, cliente: TestClient, titular: Usuario, pin: str
    ) -> None:
        assert _redefinir(cliente, titular, "123456", pin=pin).status_code == 422

    def test_redefinir_desbloqueia_a_conta(
        self,
        cliente: TestClient,
        titular: Usuario,
        correio: EmailCapturado,
        sessao: Session,
    ) -> None:
        titular.bloqueado_ate = datetime.now(UTC) + timedelta(minutes=5)
        titular.tentativas = 3
        sessao.commit()
        assert _login(cliente, titular, PIN_ATUAL).status_code == 429

        _pedir_codigo(cliente, titular)
        assert _redefinir(cliente, titular, correio.ultimo_codigo()).status_code == 200

        assert _login(cliente, titular, NOVO_PIN).status_code == 200
        sessao.refresh(titular)
        assert titular.tentativas == 0
        assert titular.bloqueado_ate is None

    def test_valkey_fora_do_ar_retorna_503(
        self, cliente: TestClient, titular: Usuario, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(recuperacao, "cliente", ValkeyFora())

        assert _redefinir(cliente, titular, "123456").status_code == 503


class TestTrocarPin:
    """PUT /api/v1/auth/pin (com login)"""

    def _token(self, usuario: Usuario) -> str:
        return criar_token(usuario.id, "pin", timedelta(hours=1), usuario.versao_token)

    def test_pin_atual_certo_troca_e_devolve_token(
        self, cliente: TestClient, titular: Usuario
    ) -> None:
        resp = cliente.put(
            TROCAR,
            json={"pin_atual": PIN_ATUAL, "novo_pin": NOVO_PIN},
            headers=_bearer(self._token(titular)),
        )

        assert resp.status_code == 200
        novo_token = resp.json()["access_token"]
        assert (
            cliente.get(ROTA_PROTEGIDA, headers=_bearer(novo_token)).status_code == 200
        )
        assert _login(cliente, titular, NOVO_PIN).status_code == 200
        assert _login(cliente, titular, PIN_ATUAL).status_code == 401

    def test_pin_atual_errado_retorna_400_e_conta_tentativa(
        self, cliente: TestClient, titular: Usuario, sessao: Session
    ) -> None:
        resp = cliente.put(
            TROCAR,
            json={"pin_atual": "000000", "novo_pin": NOVO_PIN},
            headers=_bearer(self._token(titular)),
        )

        assert resp.status_code == 400
        assert resp.json()["detail"] == Message.PIN_ATUAL_ERRADO.message
        sessao.refresh(titular)
        assert titular.tentativas == 1
        assert _login(cliente, titular, PIN_ATUAL).status_code == 200

    def test_5_erros_bloqueiam_a_conta(
        self, cliente: TestClient, titular: Usuario
    ) -> None:
        token = self._token(titular)
        respostas = [
            cliente.put(
                TROCAR,
                json={"pin_atual": "000000", "novo_pin": NOVO_PIN},
                headers=_bearer(token),
            ).status_code
            for _ in range(Attempts.MAX_TENTATIVAS.value)
        ]

        assert respostas == [400, 400, 400, 400, 429]
        assert _login(cliente, titular, PIN_ATUAL).status_code == 429

    def test_sem_login_retorna_401(self, cliente: TestClient) -> None:
        resp = cliente.put(TROCAR, json={"pin_atual": PIN_ATUAL, "novo_pin": NOVO_PIN})
        assert resp.status_code == 401

    def test_novo_pin_invalido_retorna_422(
        self, cliente: TestClient, titular: Usuario
    ) -> None:
        resp = cliente.put(
            TROCAR,
            json={"pin_atual": PIN_ATUAL, "novo_pin": "12"},
            headers=_bearer(self._token(titular)),
        )
        assert resp.status_code == 422


class TestVersaoDoToken:
    """Sessões antigas caem quando o PIN muda."""

    def test_token_antigo_recebe_401_depois_de_trocar_o_pin(
        self, cliente: TestClient, titular: Usuario
    ) -> None:
        antigo = criar_token(titular.id, "pin", timedelta(hours=1), 0)
        cliente.put(
            TROCAR,
            json={"pin_atual": PIN_ATUAL, "novo_pin": NOVO_PIN},
            headers=_bearer(antigo),
        )

        assert cliente.get(ROTA_PROTEGIDA, headers=_bearer(antigo)).status_code == 401

    def test_token_antigo_recebe_401_depois_de_redefinir_o_pin(
        self, cliente: TestClient, titular: Usuario, correio: EmailCapturado
    ) -> None:
        antigo = criar_token(titular.id, "pin", timedelta(hours=1), 0)
        _pedir_codigo(cliente, titular)
        _redefinir(cliente, titular, correio.ultimo_codigo())

        assert cliente.get(ROTA_PROTEGIDA, headers=_bearer(antigo)).status_code == 401

    def test_token_sem_versao_vale_enquanto_o_pin_nao_muda(
        self, cliente: TestClient, titular: Usuario
    ) -> None:
        # Tokens emitidos antes deste PR não têm o campo "ver"
        agora = datetime.now(UTC)
        token = jwt.encode(
            {
                "sub": str(titular.id),
                "perfil": "titular",
                "metodo": "pin",
                "iat": agora,
                "exp": agora + timedelta(hours=1),
            },
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITMO,
        )

        assert cliente.get(ROTA_PROTEGIDA, headers=_bearer(token)).status_code == 200


class TestVersaoDoTokenNoWebSocket:
    """WebSocket /ws"""

    @pytest.fixture(autouse=True)
    def ws_sem_banco_nem_valkey(
        self, sessao: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # O /ws abre a própria sessão do banco: aponta para a sessão do teste
        monkeypatch.setattr(
            router_tempo_real, "SessaoLocal", lambda: nullcontext(sessao)
        )

        async def sem_eventos(_usuario_id):
            await asyncio.Event().wait()
            yield  # pragma: no cover

        monkeypatch.setattr(eventos, "ouvir", sem_eventos)

    def test_token_na_versao_atual_conecta(
        self, cliente: TestClient, titular: Usuario
    ) -> None:
        token = criar_token(titular.id, "pin", timedelta(hours=1), titular.versao_token)

        with cliente.websocket_connect("/ws") as ws:
            ws.send_json({"token": token})
            assert ws.receive_json() == {"tipo": "conectado"}

    def test_token_antigo_e_recusado_com_1008(
        self, cliente: TestClient, titular: Usuario, sessao: Session
    ) -> None:
        antigo = criar_token(titular.id, "pin", timedelta(hours=1), 0)
        titular.versao_token = 1  # como se o PIN tivesse sido trocado
        sessao.commit()

        with cliente.websocket_connect("/ws") as ws:
            ws.send_json({"token": antigo})
            with pytest.raises(WebSocketDisconnect) as erro:
                ws.receive_json()

        assert erro.value.code == 1008
