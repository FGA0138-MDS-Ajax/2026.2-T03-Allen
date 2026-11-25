"""hash do telefone na tblUsuario (RF03/RNF05)

Revision ID: 0006
Revises: b04c899e4d41
Create Date: 2026-11-10

Migra nuTelefone (texto puro) para hashTelefone (HMAC-SHA256 com SECRET_KEY).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "b04c899e4d41"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("tblUsuario")}

    if "hashTelefone" not in cols:
        op.add_column(
            "tblUsuario", sa.Column("hashTelefone", sa.String(255), nullable=True)
        )

    if "nuTelefone" in cols:
        # Migra o telefone em texto para HMAC sem expor o segredo no log.
        bind.execute(
            sa.text(
                """
                CREATE OR REPLACE FUNCTION _hmac_sha256(key text, data text)
                RETURNS text LANGUAGE plpgsql IMMUTABLE AS $$
                BEGIN
                    RETURN encode(hmac(key::bytea, data::bytea, 'sha256'), 'hex');
                END;
                $$;
                """
            )
        )

        import os

        secret = os.getenv("SECRET_KEY")
        if not secret:
            raise RuntimeError(
                "SECRET_KEY não definida no ambiente. Export antes de rodar a migration."
            )

        bind.execute(
            sa.text(
                'UPDATE "tblUsuario" SET "hashTelefone" = '
                '_hmac_sha256(:secret, "nuTelefone") WHERE "hashTelefone" IS NULL'
            ),
            {"secret": secret},
        )
    else:
        hashes_vazios = bind.scalar(
            sa.text('SELECT count(*) FROM "tblUsuario" WHERE "hashTelefone" IS NULL')
        )
        if hashes_vazios:
            raise RuntimeError(
                "Não é possível gerar hashTelefone: há registros sem hashTelefone "
                "e a coluna nuTelefone não existe para recuperar os números."
            )

    op.alter_column("tblUsuario", "hashTelefone", nullable=False)

    unicas = insp.get_unique_constraints("tblUsuario")
    if not any(constraint["column_names"] == ["hashTelefone"] for constraint in unicas):
        op.create_unique_constraint(
            "tblusuario_hashtel_unique", "tblUsuario", ["hashTelefone"]
        )

    if "nuTelefone" in cols:
        op.drop_column("tblUsuario", "nuTelefone")

    if "nuTelefone" in cols:
        bind.execute(sa.text("DROP FUNCTION _hmac_sha256(text, text)"))


def downgrade() -> None:
    # Recria nuTelefone (não dá para reverter o hash -> texto)
    op.add_column("tblUsuario", sa.Column("nuTelefone", sa.String(255), nullable=True))
    op.drop_constraint("tblusuario_hashtel_unique", "tblUsuario", type_="unique")
    op.drop_column("tblUsuario", "hashTelefone")
