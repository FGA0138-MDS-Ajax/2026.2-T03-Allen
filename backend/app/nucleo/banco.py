import sqlite3
import uuid
from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.nucleo.config import settings


def url_sqlalchemy(url: str) -> str:
    """Converte a URL do Postgres para usar o driver psycopg 3."""
    for prefixo in ("postgresql://", "postgres://"):
        if url.startswith(prefixo):
            return "postgresql+psycopg://" + url.removeprefix(prefixo)
    return url


@event.listens_for(Engine, "connect")
def _ao_conectar_sqlite(conexao_dbapi, _):
    if isinstance(conexao_dbapi, sqlite3.Connection):
        conexao_dbapi.create_function("gen_random_uuid", 0, lambda: str(uuid.uuid4()))


argumentos_extras = {}
if settings.DATABASE_URL.startswith("sqlite"):
    argumentos_extras["connect_args"] = {"check_same_thread": False}
else:
    argumentos_extras["pool_pre_ping"] = True

engine = create_engine(url_sqlalchemy(settings.DATABASE_URL), **argumentos_extras)
SessaoLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def obter_sessao() -> Iterator[Session]:
    with SessaoLocal() as sessao:
        yield sessao
