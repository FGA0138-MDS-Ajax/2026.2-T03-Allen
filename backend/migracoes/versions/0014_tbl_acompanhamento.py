"""tblAcompanhamento: convites de acompanhante (RF06)

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-25

No Supabase a tabela já existe (sem noStatus/dhRevogacao e com icPodeEditar NOT NULL),
então lá a migration só completa o que falta. Em bancos vazios (desenvolvimento local
e CI) ela cria a tabela inteira.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABELA = "tblAcompanhamento"


def upgrade() -> None:
    inspetor = sa.inspect(op.get_bind())
    if not inspetor.has_table(TABELA):
        op.create_table(
            TABELA,
            sa.Column(
                "idUsuarioTitular",
                sa.Uuid(),
                sa.ForeignKey("tblUsuario.idUsuario"),
                primary_key=True,
            ),
            sa.Column(
                "idUsuarioAcompanhante",
                sa.Uuid(),
                sa.ForeignKey("tblUsuario.idUsuario"),
                primary_key=True,
            ),
            sa.Column("icPodeEditar", sa.Boolean(), nullable=True),
            sa.Column("dhAceite", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "dhCriacao",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "noStatus",
                sa.String(),
                server_default="pendente",
                nullable=False,
            ),
            sa.Column("dhRevogacao", sa.DateTime(timezone=True), nullable=True),
        )
        return

    colunas = {c["name"] for c in inspetor.get_columns(TABELA)}
    op.alter_column(TABELA, "icPodeEditar", existing_type=sa.Boolean(), nullable=True)
    if "noStatus" not in colunas:
        # server_default preenche as linhas que já existem
        op.add_column(
            TABELA,
            sa.Column(
                "noStatus", sa.String(), server_default="pendente", nullable=False
            ),
        )
    if "dhRevogacao" not in colunas:
        op.add_column(
            TABELA, sa.Column("dhRevogacao", sa.DateTime(timezone=True), nullable=True)
        )


def downgrade() -> None:
    # Não derruba a tabela: no Supabase ela já existia antes desta migration
    op.drop_column(TABELA, "dhRevogacao")
    op.drop_column(TABELA, "noStatus")
