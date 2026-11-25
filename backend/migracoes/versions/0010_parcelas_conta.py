"""tblConta: parcelas de compra parcelada (RF37)

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-14

Cada parcela é uma conta. nuParcela é o número dela (1, 2, 3...) e nuTotalParcelas, quantas
a compra tem. As parcelas da mesma compra ficam ligadas à primeira pela idContaOrigem.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    colunas = {
        coluna["name"] for coluna in sa.inspect(op.get_bind()).get_columns("tblConta")
    }
    if "nuParcela" not in colunas:
        op.add_column("tblConta", sa.Column("nuParcela", sa.Integer(), nullable=True))
    if "nuTotalParcelas" not in colunas:
        op.add_column(
            "tblConta", sa.Column("nuTotalParcelas", sa.Integer(), nullable=True)
        )


def downgrade() -> None:
    op.drop_column("tblConta", "nuTotalParcelas")
    op.drop_column("tblConta", "nuParcela")
