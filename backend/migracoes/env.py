from alembic import context
from sqlalchemy import engine_from_config, pool

from app.modulos.contas import modelos as modelos_contas  # noqa: F401
from app.modulos.identidade import modelos  # noqa: F401  (registra as tabelas)
from app.modulos.transacoes import modelos as modelos_transacoes  # noqa: F401
from app.nucleo.banco import Base, url_sqlalchemy
from app.nucleo.config import settings

config = context.config
config.set_main_option("sqlalchemy.url", url_sqlalchemy(settings.DATABASE_URL))
target_metadata = Base.metadata


def incluir_objeto(objeto, nome, tipo, refletido, comparar_com):
    # O banco já tem tabelas que ainda não têm model aqui (tblConta, tblTransacao...).
    # Sem este filtro, o autogenerate proporia apagá-las.
    return not (tipo == "table" and refletido and comparar_com is None)


def rodar_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        include_object=incluir_objeto,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def rodar_online() -> None:
    conexao_engine = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with conexao_engine.connect() as conexao:
        context.configure(
            connection=conexao,
            target_metadata=target_metadata,
            include_object=incluir_objeto,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    rodar_offline()
else:
    rodar_online()
