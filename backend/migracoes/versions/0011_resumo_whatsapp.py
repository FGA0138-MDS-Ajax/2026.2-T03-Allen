"""preferência do resumo periódico no WhatsApp (RF24)

Revision ID: 0011
Revises: dae0c2713ca6
Create Date: 2026-11-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "dae0c2713ca6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Ligado por padrão: a pessoa desliga respondendo "parar resumo" no WhatsApp
    cols = [c["name"] for c in sa.inspect(op.get_bind()).get_columns("tblUsuario")]
    if "icResumoAtivo" not in cols:
        op.add_column(
            "tblUsuario",
            sa.Column(
                "icResumoAtivo",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            ),
        )


def downgrade() -> None:
    cols = [c["name"] for c in sa.inspect(op.get_bind()).get_columns("tblUsuario")]
    if "icResumoAtivo" in cols:
        op.drop_column("tblUsuario", "icResumoAtivo")
