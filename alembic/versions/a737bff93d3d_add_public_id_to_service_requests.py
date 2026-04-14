"""add public_id_to_service_requests

Revision ID: a737bff93d3d
Revises: 6fb9668250c5
Create Date: 2026-01-15 10:26:16.276439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a737bff93d3d'
down_revision: Union[str, Sequence[str], None] = '6fb9668250c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "service_requests",
        sa.Column(
            "public_id",
            sa.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()")
        )
    )
    op.create_index(
        "ix_service_requests_public_id",
        "service_requests",
        ["public_id"],
        unique=True
    )


def downgrade():
    op.drop_index("ix_service_requests_public_id", table_name="service_requests")
    op.drop_column("service_requests", "public_id")
