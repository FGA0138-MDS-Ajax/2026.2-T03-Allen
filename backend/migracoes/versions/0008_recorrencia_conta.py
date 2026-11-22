"""tblConta: conta fixa mensal (RF26)

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-14

icRecorrente marca a conta que se repete todo mês. idContaOrigem liga cada mês à
primeira conta da série.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tblConta",
        sa.Column(
            "icRecorrente", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "tblConta",
        sa.Column(
            "idContaOrigem",
            sa.Uuid(),
            sa.ForeignKey("tblConta.idConta", name="tblconta_idcontaorigem_foreign"),
            nullable=True,
        ),
    )
    
TIPOS = ("entrada", "saida")
ORIGENS = (
    "manual",
    "whatsapp_texto",
    "whatsapp_audio",
    "whatsapp_foto",
    "qrcode_nf",
    "extrato",
    "conta",
)

def upgrade() -> None:
    sa.Column("recorrente", sa.Boolean(), nullable=False, server_default=sa.false())
    sa.Column(
        "idContaOrigem", sa.Uuid(), sa.ForeignKey("tblConta.idConta"), nullable=True
    )

def downgrade() -> None:
    op.drop_column("tblConta", "idContaOrigem")
    op.drop_column("tblConta", "icRecorrente")
