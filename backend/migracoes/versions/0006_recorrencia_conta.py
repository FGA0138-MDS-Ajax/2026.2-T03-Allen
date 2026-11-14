from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

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
    pass
