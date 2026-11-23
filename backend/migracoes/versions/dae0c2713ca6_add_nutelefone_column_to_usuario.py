"""add nuTelefone column to usuario

Revision ID: dae0c2713ca6
Revises: 0010
Create Date: 2026-11-22 16:35:41.699360

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "dae0c2713ca6"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # A 0006 apagou o nuTelefone (só o hash ficou); o lembrete por WhatsApp (RF28)
    # precisa do número de volta. Banco novo: a coluna não existe e é criada aqui.
    # Quem já cadastrou antes desta migration fica sem número (o hash não volta a
    # texto), por isso a coluna aceita nulo; o envio já pula quem não tem telefone.
    cols = [c["name"] for c in sa.inspect(op.get_bind()).get_columns("tblUsuario")]
    if "nuTelefone" not in cols:
        op.add_column(
            "tblUsuario", sa.Column("nuTelefone", sa.String(255), nullable=True)
        )
        op.create_unique_constraint(
            "tblusuario_nutelefone_unique", "tblUsuario", ["nuTelefone"]
        )


def downgrade() -> None:
    cols = [c["name"] for c in sa.inspect(op.get_bind()).get_columns("tblUsuario")]
    if "nuTelefone" in cols:
        op.drop_column("tblUsuario", "nuTelefone")
