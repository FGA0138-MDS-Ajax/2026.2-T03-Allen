"""tblAviso: lembretes de vencimento já enviados (RF28, RF29)

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-24

No Supabase a tabela já existe (com a mesma estrutura), então aqui ela só é criada em
bancos vazios (desenvolvimento local e CI). Os "enums" são VARCHAR com CHECK, como lá.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MOMENTOS = ("antecipado", "no_dia", "atrasado")
CANAIS = ("app", "whatsapp")


def upgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("tblAviso"):
        return

    op.create_table(
        "tblAviso",
        sa.Column("idAviso", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "idConta",
            sa.Uuid(),
            sa.ForeignKey("tblConta.idConta"),
            nullable=False,
        ),
        sa.Column("noMomento", sa.String(255), nullable=False),
        sa.Column("noCanal", sa.String(255), nullable=False),
        sa.Column("coMensagemWhatsApp", sa.Text(), nullable=True),
        sa.Column(
            "dhEnvio",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            sa.column("noMomento").in_(MOMENTOS), name="tblAviso_noMomento_check"
        ),
        sa.CheckConstraint(
            sa.column("noCanal").in_(CANAIS), name="tblAviso_noCanal_check"
        ),
        sa.UniqueConstraint(
            "idConta",
            "noMomento",
            "noCanal",
            name="tblaviso_idconta_nomomento_nocanal_unique",
        ),
    )


def downgrade() -> None:
    # Não apaga a tabela: no Supabase ela já existia antes desta migration
    pass
