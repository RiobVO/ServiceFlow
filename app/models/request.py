from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.core.enums import RequestStatus
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

import uuid


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid.uuid4,
        index=True,
    )

    status: Mapped[RequestStatus] = mapped_column(
        SAEnum(RequestStatus),
        default=RequestStatus.NEW,
        nullable=False,
    )

    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_to_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    created_by = relationship(
        "User",
        foreign_keys=[created_by_user_id],
        back_populates="created_requests",
    )
    assigned_to = relationship(
        "User",
        foreign_keys=[assigned_to_user_id],
        back_populates="assigned_requests",
    )
