"""remove phone_number from users

Revision ID: f2787a094c64
Revises: 219ca10c384c
Create Date: 2026-01-13 17:07:47.176093

"""
from alembic import op
import sqlalchemy as sa


revision = "f2787a094c64"
down_revision = "219ca10c384c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = [c["name"] for c in inspector.get_columns("users")]
    if "phone_number" in columns:
        op.drop_column("users", "phone_number")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = [c["name"] for c in inspector.get_columns("users")]
    if "phone_number" not in columns:
        op.add_column(
            "users",
            sa.Column("phone_number", sa.String(length=50), nullable=True),
        )
