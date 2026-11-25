"""e-mail obrigatório e PIN opcional na tblUsuario

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-20

hashUsuario passa a guardar o hash da senha; o PIN fica em hashPin.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspetor = sa.inspect(bind)
    colunas = {coluna["name"] for coluna in inspetor.get_columns("tblUsuario")}

    if "noEmail" not in colunas:
        op.add_column(
            "tblUsuario", sa.Column("noEmail", sa.String(255), nullable=False)
        )

    unicas = inspetor.get_unique_constraints("tblUsuario")
    if not any(constraint["column_names"] == ["noEmail"] for constraint in unicas):
        op.create_unique_constraint(
            "tblusuario_noemail_unique", "tblUsuario", ["noEmail"]
        )

    if "hashPin" not in colunas:
        op.add_column("tblUsuario", sa.Column("hashPin", sa.Text(), nullable=True))


def downgrade() -> None:
    # O schema pode existir antes do Alembic; não há como saber quais itens foram
    # criados por esta migration sem arriscar remover colunas/constraints preexistentes.
    pass
