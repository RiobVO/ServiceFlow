"""add_extended_fields_to_request_logs

Revision ID: 6fb9668250c5
Revises: f2787a094c64
Create Date: 2026-01-14 11:39:36.760352

"""
from alembic import op
import sqlalchemy as sa

revision = "6fb9668250c5"
down_revision = "f2787a094c64"  # последняя твоя миграция на сейчас
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "request_logs",
        sa.Column("client_ip", sa.String(length=45), nullable=True),
    )
    op.add_column(
        "request_logs",
        sa.Column("user_agent", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "request_logs",
        sa.Column("comment", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "request_logs",
        sa.Column("source", sa.String(length=20), nullable=False, server_default="API"),
    )
    # после миграции можно убрать server_default, если хочешь, через отдельную мигру


def downgrade() -> None:
    op.drop_column("request_logs", "source")
    op.drop_column("request_logs", "comment")
    op.drop_column("request_logs", "user_agent")
    op.drop_column("request_logs", "client_ip")

