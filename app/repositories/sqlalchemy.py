"""SQLAlchemy-реализация репозиториев.

Никаких commit/rollback здесь — транзакция управляется Unit of Work.
Все репозитории работают в рамках переданной Session.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.enums import RequestStatus, UserRole
from app.models.idempotency import IdempotencyKey
from app.models.outbox import OutboxEvent
from app.models.request import ServiceRequest
from app.models.request_log import RequestLog
from app.models.user import User


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get(self, user_id: int) -> User | None:
        return self._s.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self._s.execute(stmt).scalar_one_or_none()

    def get_by_api_key_prefix(self, prefix: str) -> list[User]:
        stmt = select(User).where(User.api_key_prefix == prefix)
        return list(self._s.scalars(stmt).all())

    def list(self, *, limit: int, offset: int) -> list[User]:
        stmt = select(User).order_by(User.id).offset(offset).limit(limit)
        return list(self._s.scalars(stmt).all())

    def count(self) -> int:
        return int(self._s.execute(select(func.count(User.id))).scalar_one())

    def any_admin(self) -> bool:
        stmt = select(User.id).where(User.role == UserRole.ADMIN).limit(1)
        return self._s.execute(stmt).first() is not None

    def add(self, user: User) -> User:
        self._s.add(user)
        self._s.flush()
        return user


class SqlAlchemyRequestRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get(self, request_id: int) -> ServiceRequest | None:
        return self._s.get(ServiceRequest, request_id)

    def list(
        self,
        *,
        status: RequestStatus | None = None,
        created_by_id: int | None = None,
        assigned_to_id: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ServiceRequest]:
        stmt = select(ServiceRequest)

        if status is not None:
            stmt = stmt.where(ServiceRequest.status == status)
        if created_by_id is not None:
            stmt = stmt.where(ServiceRequest.created_by_user_id == created_by_id)
        if assigned_to_id is not None:
            stmt = stmt.where(ServiceRequest.assigned_to_user_id == assigned_to_id)
        if date_from is not None:
            stmt = stmt.where(ServiceRequest.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(ServiceRequest.created_at <= date_to)

        stmt = stmt.order_by(ServiceRequest.created_at.desc()).offset(offset).limit(limit)
        return list(self._s.scalars(stmt).all())

    def list_by_creator(
        self, creator_id: int, *, limit: int, offset: int
    ) -> list[ServiceRequest]:
        stmt = (
            select(ServiceRequest)
            .where(ServiceRequest.created_by_user_id == creator_id)
            .order_by(desc(ServiceRequest.id))
            .offset(offset)
            .limit(limit)
        )
        return list(self._s.scalars(stmt).all())

    def list_by_assignee(
        self, assignee_id: int, *, limit: int, offset: int
    ) -> list[ServiceRequest]:
        stmt = (
            select(ServiceRequest)
            .where(ServiceRequest.assigned_to_user_id == assignee_id)
            .order_by(desc(ServiceRequest.created_at))
            .offset(offset)
            .limit(limit)
        )
        return list(self._s.scalars(stmt).all())

    def list_queue(self, *, limit: int, offset: int) -> list[ServiceRequest]:
        stmt = (
            select(ServiceRequest)
            .where(
                ServiceRequest.status == RequestStatus.NEW,
                ServiceRequest.assigned_to_user_id.is_(None),
            )
            .order_by(desc(ServiceRequest.created_at))
            .offset(offset)
            .limit(limit)
        )
        return list(self._s.scalars(stmt).all())

    def add(self, request: ServiceRequest) -> ServiceRequest:
        self._s.add(request)
        self._s.flush()
        return request

    def count(
        self,
        *,
        status: RequestStatus | None = None,
        created_by_id: int | None = None,
        assigned_to_id: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        stmt = select(func.count(ServiceRequest.id))
        if status is not None:
            stmt = stmt.where(ServiceRequest.status == status)
        if created_by_id is not None:
            stmt = stmt.where(ServiceRequest.created_by_user_id == created_by_id)
        if assigned_to_id is not None:
            stmt = stmt.where(ServiceRequest.assigned_to_user_id == assigned_to_id)
        if date_from is not None:
            stmt = stmt.where(ServiceRequest.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(ServiceRequest.created_at <= date_to)
        return int(self._s.execute(stmt).scalar_one())

    def count_by_creator(self, creator_id: int) -> int:
        stmt = select(func.count(ServiceRequest.id)).where(
            ServiceRequest.created_by_user_id == creator_id
        )
        return int(self._s.execute(stmt).scalar_one())

    def count_by_assignee(self, assignee_id: int) -> int:
        stmt = select(func.count(ServiceRequest.id)).where(
            ServiceRequest.assigned_to_user_id == assignee_id
        )
        return int(self._s.execute(stmt).scalar_one())

    def count_queue(self) -> int:
        stmt = select(func.count(ServiceRequest.id)).where(
            ServiceRequest.status == RequestStatus.NEW,
            ServiceRequest.assigned_to_user_id.is_(None),
        )
        return int(self._s.execute(stmt).scalar_one())


class SqlAlchemyOutboxRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, event: OutboxEvent) -> OutboxEvent:
        self._s.add(event)
        self._s.flush()
        return event

    def fetch_pending(self, limit: int = 50) -> list[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.processed_at.is_(None))
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(self._s.scalars(stmt).all())


class SqlAlchemyIdempotencyRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get(self, *, user_id: int, method: str, path: str, key: str) -> IdempotencyKey | None:
        stmt = select(IdempotencyKey).where(
            IdempotencyKey.user_id == user_id,
            IdempotencyKey.method == method,
            IdempotencyKey.path == path,
            IdempotencyKey.key == key,
        )
        return self._s.execute(stmt).scalar_one_or_none()

    def add(self, record: IdempotencyKey) -> IdempotencyKey:
        self._s.add(record)
        self._s.flush()
        return record


class SqlAlchemyRequestLogRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, log: RequestLog) -> RequestLog:
        self._s.add(log)
        self._s.flush()
        return log

    def list_for_request(self, request_id: int) -> list[RequestLog]:
        stmt = (
            select(RequestLog)
            .where(RequestLog.request_id == request_id)
            .order_by(RequestLog.timestamp.asc())
        )
        return list(self._s.scalars(stmt).all())
