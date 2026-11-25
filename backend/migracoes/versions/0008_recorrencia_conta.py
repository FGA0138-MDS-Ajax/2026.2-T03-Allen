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
    bind = op.get_bind()
    inspetor = sa.inspect(bind)
    colunas = {coluna["name"] for coluna in inspetor.get_columns("tblConta")}
    if "icRecorrente" not in colunas:
        op.add_column(
            "tblConta",
            sa.Column(
                "icRecorrente", sa.Boolean(), nullable=False, server_default=sa.false()
            ),
        )

    chaves = inspetor.get_foreign_keys("tblConta")
    tem_fk_origem = any(
        chave["constrained_columns"] == ["idContaOrigem"]
        and chave["referred_table"] == "tblConta"
        for chave in chaves
    )
    if "idContaOrigem" not in colunas:
        op.add_column(
            "tblConta",
            sa.Column(
                "idContaOrigem",
                sa.Uuid(),
                sa.ForeignKey(
                    "tblConta.idConta", name="tblconta_idcontaorigem_foreign"
                ),
                nullable=True,
            ),
        )
    elif not tem_fk_origem:
        op.create_foreign_key(
            "tblconta_idcontaorigem_foreign",
            "tblConta",
            "tblConta",
            ["idContaOrigem"],
            ["idConta"],
        )


def downgrade() -> None:
    op.drop_column("tblConta", "idContaOrigem")
    op.drop_column("tblConta", "icRecorrente")
