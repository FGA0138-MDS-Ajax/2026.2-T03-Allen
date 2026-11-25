"""Testes de GET /auth/contas-com-acompanhantes (RF06)."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modulos.identidade.modelos import Acompanhante, Usuario
from app.modulos.identidade.seguranca import criar_token, gerar_hash, hash_telefone

URL = "/api/v1/auth/contas-com-acompanhantes"


def _criar_usuario(sessao: Session, nome: str) -> Usuario:
    telefone = "55619" + uuid.uuid4().hex[:8]
    u = Usuario(
        id=uuid.uuid4(),
        nome=nome,
        hash_telefone=hash_telefone(telefone),
        email=f"{uuid.uuid4().hex[:8]}@vero.com",
        hash_pin=gerar_hash("123456"),
        tentativas=0,
    )
    sessao.add(u)
    sessao.flush()
    return u


def _criar_convite(
    sessao: Session, titular: Usuario, acompanhante: Usuario, status: str
) -> Acompanhante:
    convite = Acompanhante(
        id_usuario_titular=titular.id,
        id_usuario_acompanhante=acompanhante.id,
        ic_pode_editar=True,
        status=status,
        dh_aceite=datetime.now(UTC) if status == "autorizado" else None,
    )
    sessao.add(convite)
    sessao.flush()
    return convite


def test_sem_convites_retorna_lista_vazia(cliente_logado: TestClient):
    resposta = cliente_logado.get(URL)

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_convite_pendente_nao_aparece_ate_ser_aceito(
    sessao: Session, cliente_logado: TestClient, usuario: Usuario
):
    acompanhante = _criar_usuario(sessao, "Ana")
    convite = _criar_convite(sessao, usuario, acompanhante, "pendente")

    assert cliente_logado.get(URL).json() == []

    convite.status = "autorizado"
    convite.dh_aceite = datetime.now(UTC)
    sessao.flush()

    dados = cliente_logado.get(URL).json()
    assert len(dados) == 1
    assert dados[0]["id"] == str(acompanhante.id)


def test_convite_autorizado_retorna_dados_do_acompanhante(
    sessao: Session, cliente_logado: TestClient, usuario: Usuario
):
    acompanhante = _criar_usuario(sessao, "Ana")
    _criar_convite(sessao, usuario, acompanhante, "autorizado")

    resposta = cliente_logado.get(URL)

    assert resposta.status_code == 200
    [item] = resposta.json()
    assert item["id"] == str(acompanhante.id)
    assert item["usuario"] == "Ana"
    assert item["pode_editar"] is True
    assert item["data_convite"] is not None
    assert item["data_aceite"] is not None


def test_lista_apenas_autorizados(
    sessao: Session, cliente_logado: TestClient, usuario: Usuario
):
    pendente = _criar_usuario(sessao, "Pendente")
    autorizado = _criar_usuario(sessao, "Autorizado")
    revogado = _criar_usuario(sessao, "Revogado")
    _criar_convite(sessao, usuario, pendente, "pendente")
    _criar_convite(sessao, usuario, autorizado, "autorizado")
    _criar_convite(sessao, usuario, revogado, "revogado")

    dados = cliente_logado.get(URL).json()

    assert [item["usuario"] for item in dados] == ["Autorizado"]


def test_nao_lista_acompanhantes_de_outro_titular(
    sessao: Session, cliente_logado: TestClient
):
    outro_titular = _criar_usuario(sessao, "Outro")
    acompanhante = _criar_usuario(sessao, "Ana")
    _criar_convite(sessao, outro_titular, acompanhante, "autorizado")

    assert cliente_logado.get(URL).json() == []


# ── Convidar, aceitar e revogar ─────────────────────────────────────


def _logar_como(cliente: TestClient, usuario: Usuario) -> None:
    token = criar_token(usuario.id, "pin", timedelta(hours=1))
    cliente.headers["Authorization"] = f"Bearer {token}"


def test_convidar_cria_convite_pendente(
    sessao: Session, cliente_logado: TestClient, usuario: Usuario
):
    acompanhante = _criar_usuario(sessao, "Ana")

    resposta = cliente_logado.post(
        "/api/v1/auth/convidar-acompanhante",
        params={"id_usuario_acompanhante": str(acompanhante.id)},
    )

    assert resposta.status_code == 201
    assert resposta.json()["convite_id"] == str(acompanhante.id)
    convite = sessao.get(Acompanhante, (usuario.id, acompanhante.id))
    assert convite is not None
    assert convite.status == "pendente"


def test_convidar_de_novo_retorna_409(sessao: Session, cliente_logado: TestClient):
    acompanhante = _criar_usuario(sessao, "Ana")
    params = {"id_usuario_acompanhante": str(acompanhante.id)}

    cliente_logado.post("/api/v1/auth/convidar-acompanhante", params=params)
    resposta = cliente_logado.post("/api/v1/auth/convidar-acompanhante", params=params)

    assert resposta.status_code == 409


def test_convidar_usuario_inexistente_ou_a_si_mesmo(
    cliente_logado: TestClient, usuario: Usuario
):
    url = "/api/v1/auth/convidar-acompanhante"
    inexistente = cliente_logado.post(
        url, params={"id_usuario_acompanhante": str(uuid.uuid4())}
    )
    si_mesmo = cliente_logado.post(
        url, params={"id_usuario_acompanhante": str(usuario.id)}
    )

    assert inexistente.status_code == 404
    assert si_mesmo.status_code == 422


def test_fluxo_aceitar_e_revogar(
    sessao: Session, cliente: TestClient, usuario: Usuario
):
    acompanhante = _criar_usuario(sessao, "Ana")
    _criar_convite(sessao, usuario, acompanhante, "pendente")

    _logar_como(cliente, acompanhante)
    aceite = cliente.post(f"/api/v1/auth/aceitar-convite/{usuario.id}")
    assert aceite.status_code == 200

    _logar_como(cliente, usuario)
    assert [i["usuario"] for i in cliente.get(URL).json()] == ["Ana"]

    revogar = cliente.post(f"/api/v1/auth/revogar-acesso/{acompanhante.id}")
    assert revogar.status_code == 200
    assert cliente.get(URL).json() == []

    # Depois de revogado dá para convidar de novo
    reconvite = cliente.post(
        "/api/v1/auth/convidar-acompanhante",
        params={"id_usuario_acompanhante": str(acompanhante.id)},
    )
    assert reconvite.status_code == 201


def test_aceitar_convite_de_outra_pessoa_retorna_404(
    sessao: Session, cliente_logado: TestClient
):
    titular = _criar_usuario(sessao, "Titular")
    convidada = _criar_usuario(sessao, "Convidada")
    _criar_convite(sessao, titular, convidada, "pendente")

    # cliente_logado é um terceiro, não a pessoa convidada
    resposta = cliente_logado.post(f"/api/v1/auth/aceitar-convite/{titular.id}")

    assert resposta.status_code == 404
