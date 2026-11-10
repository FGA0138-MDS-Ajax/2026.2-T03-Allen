from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.nucleo.config import settings


def url_sqlalchemy(url: str) -> str:
    """Converte a URL do Postgres para usar o driver psycopg 3."""
    for prefixo in ("postgresql://", "postgres://"):
        if url.startswith(prefixo):
            return "postgresql+psycopg://" + url.removeprefix(prefixo)
    return url


engine = create_engine(url_sqlalchemy(settings.DATABASE_URL), pool_pre_ping=True)
SessaoLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def obter_sessao() -> Iterator[Session]:
    with SessaoLocal() as sessao:
        yield sessao
