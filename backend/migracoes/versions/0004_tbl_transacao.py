"""tblTransacao: registro de gastos e receitas (RF17)

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-03

No Supabase a tabela já existe, então aqui ela só é criada em bancos vazios
(desenvolvimento local e CI), igual à do Supabase: os "enums" são VARCHAR com CHECK.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
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

    op.create_table(
        "tblTransacao",
        sa.Column(
            "idTransacao",
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
        sa.Column(
            "noTipoTransacao",
            sa.String(255),
            nullable=False,
        ),
        sa.Column("vrTransacao", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "dtTransacao",
            sa.Date(),
            nullable=False,
            server_default=sa.text("CURRENT_DATE"),
        ),
        sa.Column("descTransacao", sa.Text(), nullable=True),
        sa.Column(
            "idCategoria",
            sa.BigInteger(),
            sa.ForeignKey("tblCategoria.idCategoria"),
            nullable=True,
        ),
        sa.Column(
            "noOrigem",
            sa.String(255),
            nullable=False,
            server_default="manual",
        ),
        sa.Column(
            "idConta",
            sa.Uuid(),
            sa.ForeignKey("tblConta.idConta"),
            nullable=True,
            unique=True,
        ),
        # tblExtratos ainda não tem migration: a coluna existe, a FK fica para depois
        sa.Column("idExtrato", sa.Uuid(), nullable=True),
        sa.Column("coChaveExterna", sa.Text(), nullable=True),
        sa.Column("pathComprovante", sa.Text(), nullable=True),
        sa.Column(
            "idUsuarioCriador",
            sa.Uuid(),
            sa.ForeignKey("tblUsuario.idUsuario"),
            nullable=True,
        ),
        sa.Column(
            "dhCriacao",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "dhAtualizacao",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            sa.column("noTipoTransacao").in_(TIPOS),
            name="tblTransacao_noTipoTransacao_check",
        ),
        sa.CheckConstraint(
            sa.column("noOrigem").in_(ORIGENS),
            name="tblTransacao_noOrigem_check",
        ),
    )
    op.create_index(
        "tbltransacao_idusuario_dttransacao_index",
        "tblTransacao",
        ["idUsuario", "dtTransacao"],
    )
    op.create_unique_constraint(
        "tbltransacao_idusuario_cochaveexterna_unique",
        "tblTransacao",
        ["idUsuario", "coChaveExterna"],
    )


def downgrade() -> None:
    # Não apaga a tabela: no Supabase ela já existia antes desta migration e tem dados
    pass
