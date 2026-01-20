from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, Column, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.core.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.EMPLOYEE, nullable=False)

    # api_key оставляем как обычный Column, чтобы не ломать существующую логику
    api_key = Column(String, unique=True, index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    created_requests = relationship(
        "ServiceRequest",
        foreign_keys="ServiceRequest.created_by_user_id",
        back_populates="created_by",
    )
    assigned_requests = relationship(
        "ServiceRequest",
        foreign_keys="ServiceRequest.assigned_to_user_id",
        back_populates="assigned_to",
    )
