"""Unit of Work.

Контроль границы транзакции и агрегация репозиториев.
Сервис получает UoW, а не Session — таким образом:
    - один commit на бизнес-операцию (атомарность записи заявки + аудит);
    - тесты могут подмешать фейковый UoW без БД.

Использование:
    with uow:
        uow.requests.add(req)
        uow.request_logs.add(log)
        uow.commit()
"""

from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session, sessionmaker

from app.database.session import SessionLocal
from app.repositories.sqlalchemy import (
    SqlAlchemyIdempotencyRepository,
    SqlAlchemyOutboxRepository,
    SqlAlchemyRequestLogRepository,
    SqlAlchemyRequestRepository,
    SqlAlchemyUserRepository,
)


class SqlAlchemyUnitOfWork:
    users: SqlAlchemyUserRepository
    requests: SqlAlchemyRequestRepository
    request_logs: SqlAlchemyRequestLogRepository
    idempotency: SqlAlchemyIdempotencyRepository
    outbox: SqlAlchemyOutboxRepository

    def __init__(self, session_factory: sessionmaker = SessionLocal) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        self.users = SqlAlchemyUserRepository(self._session)
        self.requests = SqlAlchemyRequestRepository(self._session)
        self.request_logs = SqlAlchemyRequestLogRepository(self._session)
        self.idempotency = SqlAlchemyIdempotencyRepository(self._session)
        self.outbox = SqlAlchemyOutboxRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self._session is not None
        try:
            if exc is not None:
                self._session.rollback()
        finally:
            self._session.close()
            self._session = None

    @property
    def session(self) -> Session:
        assert self._session is not None, "UoW used outside of context"
        return self._session

    def commit(self) -> None:
        assert self._session is not None
        self._session.commit()

    def rollback(self) -> None:
        assert self._session is not None
        self._session.rollback()

    def flush(self) -> None:
        assert self._session is not None
        self._session.flush()

    def refresh(self, obj: object) -> None:
        assert self._session is not None
        self._session.refresh(obj)
