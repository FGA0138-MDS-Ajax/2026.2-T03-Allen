"""tblInvestimento: cadastro de investimentos em CDB e renda fixa (RF35)

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-24

Guarda o que os bancos guardam de cada aplicação: produto, instituição, valor, data da
aplicação, vencimento, rentabilidade contratada (prefixada ou % do CDI) e liquidez. O
valor atual não fica no banco: é calculado a partir destes dados (RF36).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TIPOS = ("cdb", "renda_fixa")
INDEXADORES = ("prefixado", "cdi")


def upgrade() -> None:
    op.create_table(
        "tblInvestimento",
        sa.Column(
            "idInvestimento",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "idUsuario",
            sa.Uuid(),
            sa.ForeignKey("tblUsuario.idUsuario"),
            nullable=False,
        ),
        sa.Column("noTipoInvestimento", sa.String(255), nullable=False),
        sa.Column("noInvestimento", sa.String(255), nullable=False),
        sa.Column("noInstituicao", sa.String(255), nullable=True),
        sa.Column("vrAplicado", sa.Numeric(12, 2), nullable=False),
        sa.Column("dtAplicacao", sa.Date(), nullable=False),
        sa.Column("dtVencimento", sa.Date(), nullable=True),
        sa.Column("noIndexador", sa.String(255), nullable=False),
        sa.Column("vrTaxa", sa.Numeric(7, 2), nullable=False),
        sa.Column(
            "icLiquidezDiaria", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "dhCriacao",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            sa.column("noTipoInvestimento").in_(TIPOS),
            name="tblInvestimento_noTipoInvestimento_check",
        ),
        sa.CheckConstraint(
            sa.column("noIndexador").in_(INDEXADORES),
            name="tblInvestimento_noIndexador_check",
        ),
        sa.CheckConstraint('"vrAplicado" > 0', name="tblInvestimento_vrAplicado_check"),
        sa.CheckConstraint('"vrTaxa" > 0', name="tblInvestimento_vrTaxa_check"),
    )
    op.create_index("tblinvestimento_idusuario_index", "tblInvestimento", ["idUsuario"])


def downgrade() -> None:
    op.drop_index("tblinvestimento_idusuario_index", table_name="tblInvestimento")
    op.drop_table("tblInvestimento")
