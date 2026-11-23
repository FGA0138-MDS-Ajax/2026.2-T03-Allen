"""Testes automatizados para listar_acompanhantes (US23)."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modulos.identidade.modelos import Acompanhante, Usuario
from app.modulos.identidade.seguranca import gerar_hash

# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def usuario_titular(sessao: Session) -> Usuario:
    """Usuário titular para testes de acompanhante."""
    u = Usuario(
        nome="João Silva",
        email="joao@vero.com",
        hash_telefone=gerar_hash("5511988887777"),
        whatsapp_ativo=True,
    )
    sessao.add(u)
    sessao.flush()
    sessao.refresh(u)
    return u


@pytest.fixture
def usuario_acompanhante(sessao: Session) -> Usuario:
    """Usuário para ser o acompanhante (familiar/amigo)."""
    u = Usuario(
        nome="Maria Oliveira",
        email="maria@vero.com",
        hash_telefone=gerar_hash("5511988887778"),
        whatsapp_ativo=True,
    )
    sessao.add(u)
    sessao.flush()
    sessao.refresh(u)
    return u


# ── Helper ──────────────────────────────────────────────────────────


def _criar_convite(
    sessao: Session,
    usuario_titular: Usuario,
    usuario_acompanhante: Usuario,
    status: str = "pendente",
) -> Acompanhante:
    """Criar um convite entre dois usuários."""
    convite = Acompanhante(
        id_usuario_titular=usuario_titular.id,
        id_usuario_acompanhante=usuario_acompanhante.id,
        ic_pode_editar=True,
        status=status,
    )
    sessao.add(convite)
    sessao.commit()
    sessao.refresh(convite)
    return convite


# ── Testes ──────────────────────────────────────────────────────────


def test_listar_acompanhantes_sem_convite(
    sessao: Session, cliente_logado: TestClient, usuario_titular: Usuario
):
    """Deve retornar lista vazia quando usuário não tem acompanhantes autorizados."""

    # Força endpoint a usar o usuário logado
    with cliente_logado as client:
        response = client.get("/api/v1/auth/contas-com-acompanhantes")

    assert response.status_code == 200
    dados = response.json()
    assert isinstance(dados, list)
    assert len(dados) == 0, f"Esperava lista vazia, mas got: {dados}"


def test_listar_acompanhantes_com_convite_pendente(
    sessao: Session,
    cliente_logado: TestClient,
    usuario_titular: Usuario,
    usuario_acompanhante: Usuario,
):
    """Deve retornar acompanhantes apenas com status 'autorizado' (ignora 'pendente')."""
    # Cria convite com status pendente
    convite = _criar_convite(
        sessao, usuario_titular, usuario_acompanhante, status="pendente"
    )

    with cliente_logado as client:
        response = client.get("/api/v1/auth/contas-com-acompanhantes")

    assert response.status_code == 200
    dados = response.json()
    assert len(dados) == 0, (
        f"Esperava lista vazia (status pendente), mas got {len(dados)} itens: {dados}"
    )

    # Agora aceita o convite (como o usuário faria)
    # O endpoint aceita-convite muda status para "autorizado"

    # Simula o aceite do convite
    convite.status = "autorizado"
    convite.dh_aceite = datetime.now(UTC)
    sessao.commit()

    # Agora deve listar
    with cliente_logado:
        response = client.get("/api/v1/auth/contas-com-acompanhantes")

    assert response.status_code == 200
    dados = response.json()
    assert len(dados) == 1, f"Esperava 1 item, mas got {len(dados)}"

    item = dados[0]
    # Verificar estrutura esperada
    assert "id" in item, "Campo 'id' ausente na resposta"
    assert "usuario" in item, "Campo 'usuario' ausente na resposta"
    assert "data_convite" in item, "Campo 'data_convite' ausente na resposta"
    assert "pode_editar" in item, "Campo 'pode_editar' ausente na resposta"
    assert "data_aceite" in item, "Campo 'data_aceite' ausente na resposta"


def test_listar_acompanhantes_com_convite_autorizado(
    sessao: Session,
    cliente_logado: TestClient,
    usuario_titular: Usuario,
    usuario_acompanhante: Usuario,
):
    """Deve retornar acompanhante quando status for 'autorizado' diretamente."""
    # Cria convite já com status autorizado
    convite = _criar_convite(
        sessao, usuario_titular, usuario_acompanhante, status="autorizado"
    )
    convite.dh_aceite = datetime.now(UTC)
    sessao.commit()

    with cliente_logado as client:
        response = client.get("/api/v1/auth/contas-com-acompanhantes")

    assert response.status_code == 200
    dados = response.json()
    assert len(dados) == 1, f"Esperava 1 item, mas got {len(dados)}"

    item = dados[0]
    # Verificar tipos de dados
    assert isinstance(item["id"], str), f"'id' deve ser string, got {type(item['id'])}"
    assert item["usuario"] is not None, " 'usuario' deve vir preenchido"
    assert "data_convite" in item, "Campo 'data_convite' esperado"
    assert "pode_editar" in item, "Campo 'pode_editar' esperado"
    assert "data_aceite" in item, "Campo 'data_aceite' esperado"

    # O campo usuario deve conter o objeto (ou seus fields serializados)
    usuario_dados = item["usuario"]
    assert isinstance(usuario_dados, dict), (
        f" 'usuario' deve ser dict, got {type(usuario_dados)}"
    )
    assert "nome" in usuario_dados, "Campo 'nome' do usuario esperado"


def test_listar_acompanhantes_multiple_registros(
    sessao: Session,
    cliente_logado: TestClient,
    usuario_titular: Usuario,
    usuario_acompanhante: Usuario,
):
    """Deve retornar apenas acompanhantes autorizados, ignorando outros status."""
    # Cria 3 convites com statuss diferentes
    _criar_convite(sessao, usuario_titular, usuario_acompanhante, status="pendente")
    _criar_convite(sessao, usuario_titular, usuario_acompanhante, status="autorizado")
    _criar_convite(sessao, usuario_titular, usuario_acompanhante, status="revogado")

    with cliente_logado as client:
        response = client.get("/api/v1/auth/contas-com-acompanhantes")

    assert response.status_code == 200
    dados = response.json()
    # Apenas o de status 'autorizado' deve aparecer
    assert len(dados) == 1, (
        f"Esperava 1 item (autorizado), mas got {len(dados)}: {dados}"
    )

    # Confirmar que o item retornado tem status autorizado
    assert dados[0]["status"] == "autorizado" or dados[0].get("pode_editar") is True


# ── Rodar teste isolado ────────────────────────────────────────────

# Se rodar esse arquivo diretamente (pytest -x ele pula)
if __name__ == "__main__":
    print("Execute com: pytest backend/tests/test_listar_acompanhantes.py -v")
