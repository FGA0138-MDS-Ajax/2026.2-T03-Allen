"""tblUsuario: versão do token, para derrubar sessões quando o PIN muda

Revision ID: 0006
Revises: b04c899e4d41
Create Date: 2026-11-10

Ao redefinir ou trocar o PIN, nuVersaoToken sobe e os tokens já emitidos, que
levam a versão antiga, deixam de valer (inclusive no /ws).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "b04c899e4d41"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tblUsuario",
        sa.Column("nuVersaoToken", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("tblUsuario", "nuVersaoToken")
