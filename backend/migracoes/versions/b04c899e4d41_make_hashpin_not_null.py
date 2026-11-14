"""make_hashpin_not_null

Revision ID: b04c899e4d41
Revises: 0005
Create Date: 2026-11-10 14:52:01.934631

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b04c899e4d41"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # isso aqui é um hash de 123456
    # esse placeholder teoricamente vai forcar o user a alterar o pin
    op.execute(
        'UPDATE "tblUsuario" SET "hashPin" = \'$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S\' WHERE "hashPin" IS NULL'
    )
    op.alter_column("tblUsuario", "hashPin", nullable=False)


def downgrade() -> None:
    op.alter_column("tblUsuario", "hashPin", nullable=True)
