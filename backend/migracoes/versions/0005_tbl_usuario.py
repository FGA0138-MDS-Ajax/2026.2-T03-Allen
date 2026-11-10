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
    if sa.inspect(op.get_bind()).has_table("tblTransacao"):
        return

    op.drop_column("tblUsuario", "hashUsuario")
    op.alter_column("tblUsuario", "noEmail", nullable=True)


def downgrade() -> None:
    pass
