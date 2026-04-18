"""enable pgcrypto

Revision ID: e665755dea52
Revises: a737bff93d3d
Create Date: 2026-01-15 15:00:36.771169
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'e665755dea52'
down_revision = 'a737bff93d3d'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")


def downgrade():
    op.execute("DROP EXTENSION IF EXISTS pgcrypto;")
