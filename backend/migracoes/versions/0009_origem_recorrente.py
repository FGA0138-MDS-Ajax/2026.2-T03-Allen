"""tblTransacao: origem "recorrente" para o lançamento automático (RF18)

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-14

O noOrigem é texto com CHECK. Recria o CHECK com o valor novo. O nome do CHECK é
procurado no banco, porque pode ser diferente no Supabase.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NOME_CHECK = "tblTransacao_noOrigem_check"
ORIGENS = (
    "manual",
    "whatsapp_texto",
    "whatsapp_audio",
    "whatsapp_foto",
    "qrcode_nf",
    "extrato",
    "conta",
)

def _trocar_check(origens: tuple[str, ...]) -> None:
    for check in sa.inspect(op.get_bind()).get_check_constraints("tblTransacao"):
        if "noOrigem" in check["sqltext"]:
            op.drop_constraint(check["name"], "tblTransacao", type_="check")
    op.create_check_constraint(
        NOME_CHECK, "tblTransacao", sa.column("noOrigem").in_(origens)
    )

def upgrade() -> None:
    _trocar_check((*ORIGENS, "recorrente"))

def downgrade() -> None:
    # Falha se ainda houver transação com origem "recorrente": apague-as antes
    _trocar_check(ORIGENS)
