"""Fixtures dos testes: banco Postgres de teste e cliente autenticado.

Os testes rodam no Postgres apontado por DATABASE_URL (no CI, o serviço postgres
do workflow). Cada teste roda numa transação desfeita no fim, então nada fica no
banco. Não aponte para o Supabase.
"""

import os
import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.main import app
from app.modulos.contas.modelos import Conta  # noqa: F401  (registra a tabela)
from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.seguranca import criar_token, gerar_hash, hash_telefone
from app.nucleo.banco import Base, obter_sessao, url_sqlalchemy
from app.nucleo.config import settings

URL_TESTE = url_sqlalchemy(settings.DATABASE_URL)


@pytest.fixture(scope="session")
def engine():
    url = make_url(URL_TESTE)
    if url.get_backend_name() != "postgresql":
        pytest.exit("Os testes precisam de um Postgres em DATABASE_URL.", returncode=4)
    if "supabase" in (url.host or ""):
        pytest.exit("DATABASE_URL aponta para o Supabase; use um banco de teste.", 4)
    motor = create_engine(url)
    Base.metadata.create_all(motor)
    yield motor
    motor.dispose()


@pytest.fixture
def sessao(engine) -> Iterator[Session]:
    """Cada teste roda numa transação que é desfeita no fim."""
    conexao = engine.connect()
    transacao = conexao.begin()
    fabrica = sessionmaker(
        bind=conexao, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    with fabrica() as s:
        yield s
    transacao.rollback()
    conexao.close()


@pytest.fixture
def usuario(sessao: Session) -> Usuario:
    telefone = "55619" + uuid.uuid4().hex[:8]
    u = Usuario(
        id=uuid.uuid4(),
        nome="Maria",
        hash_telefone=hash_telefone(telefone),
        email=f"maria{uuid.uuid4().hex[:8]}@vero.com",
        hash_pin=gerar_hash("123456"),
        tentativas=0,
    )
    u.telefone = telefone  # para resposta da API
    sessao.add(u)
    sessao.flush()
    sessao.refresh(u)
    return u


@pytest.fixture
def cliente(sessao: Session) -> Iterator[TestClient]:
    app.dependency_overrides[obter_sessao] = lambda: sessao
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def cliente_logado(cliente: TestClient, usuario: Usuario) -> TestClient:
    from datetime import timedelta

    token = criar_token(usuario.id, "pin", timedelta(hours=1))
    cliente.headers["Authorization"] = f"Bearer {token}"
    return cliente
