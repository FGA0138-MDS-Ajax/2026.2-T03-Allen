"""merge heads acompanhante

Revision ID: 450d4513d145
Revises: 4a46ca7073a3, 53d93cc6a82c, dae0c2713ca6
Create Date: 2026-11-22 20:48:08.475578

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '450d4513d145'
down_revision: str | None = ('4a46ca7073a3', '53d93cc6a82c', 'dae0c2713ca6')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
