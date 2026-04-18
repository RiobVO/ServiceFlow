from datetime import datetime

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class OutboxEvent(Base):
    """Outbox — атомарно пишется в транзакции с бизнес-операцией.

    Воркер отдельным процессом забирает processed_at IS NULL,
    публикует наружу и помечает.
    """

    __tablename__ = "outbox_events"
    __table_args__ = (
        # Под горячий запрос воркера: processed_at IS NULL ORDER BY created_at.
        Index(
            "ix_outbox_events_pending",
            "created_at",
            postgresql_where="processed_at IS NULL",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
