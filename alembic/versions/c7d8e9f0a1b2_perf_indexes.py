"""perf indexes for service_requests and request_logs

Revision ID: c7d8e9f0a1b2
Revises: b1a2c3d4e5f6
Create Date: 2026-04-18 00:10:00.000000

Составные индексы под реальные паттерны выборок:
    - /requests?status=... → ix_service_requests_status_created_at
    - /assigned-to-me     → ix_service_requests_assignee_status
    - /my                 → ix_service_requests_creator_created_at
    - /queue              → ix_service_requests_queue (partial)
    - история заявки      → ix_request_logs_request_timestamp
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "b1a2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_service_requests_status_created_at",
        "service_requests",
        ["status", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_service_requests_assignee_status",
        "service_requests",
        ["assigned_to_user_id", "status"],
    )
    op.create_index(
        "ix_service_requests_creator_created_at",
        "service_requests",
        ["created_by_user_id", sa.text("created_at DESC")],
    )
    # Частичный индекс под очередь: покрывает узкий горячий набор строк.
    op.create_index(
        "ix_service_requests_queue",
        "service_requests",
        [sa.text("created_at DESC")],
        postgresql_where=sa.text("status = 'NEW' AND assigned_to_user_id IS NULL"),
    )
    op.create_index(
        "ix_request_logs_request_timestamp",
        "request_logs",
        ["request_id", "timestamp"],
    )


def downgrade() -> None:
    op.drop_index("ix_request_logs_request_timestamp", table_name="request_logs")
    op.drop_index("ix_service_requests_queue", table_name="service_requests")
    op.drop_index("ix_service_requests_creator_created_at", table_name="service_requests")
    op.drop_index("ix_service_requests_assignee_status", table_name="service_requests")
    op.drop_index("ix_service_requests_status_created_at", table_name="service_requests")
