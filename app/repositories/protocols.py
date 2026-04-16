"""Протоколы репозиториев.

Используем структурную типизацию (Protocol), чтобы сервисы зависели
от контрактов, а не от конкретных SQLAlchemy-реализаций. Тестам
проще подмешать fake — просто класс, реализующий те же методы.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from app.core.enums import RequestStatus
from app.models.request import ServiceRequest
from app.models.request_log import RequestLog
from app.models.user import User


@runtime_checkable
class UserRepository(Protocol):
    def get(self, user_id: int) -> User | None: ...
    def get_by_email(self, email: str) -> User | None: ...
    def get_by_api_key_prefix(self, prefix: str) -> list[User]: ...
    def list(self, *, limit: int, offset: int) -> list[User]: ...
    def count(self) -> int: ...
    def any_admin(self) -> bool: ...
    def add(self, user: User) -> User: ...


@runtime_checkable
class RequestRepository(Protocol):
    def get(self, request_id: int) -> ServiceRequest | None: ...
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
    ) -> list[ServiceRequest]: ...
    def list_by_creator(
        self, creator_id: int, *, limit: int, offset: int
    ) -> list[ServiceRequest]: ...
    def list_by_assignee(
        self, assignee_id: int, *, limit: int, offset: int
    ) -> list[ServiceRequest]: ...
    def list_queue(self, *, limit: int, offset: int) -> list[ServiceRequest]: ...
    def add(self, request: ServiceRequest) -> ServiceRequest: ...
    def count(
        self,
        *,
        status: RequestStatus | None = None,
        created_by_id: int | None = None,
        assigned_to_id: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int: ...
    def count_by_creator(self, creator_id: int) -> int: ...
    def count_by_assignee(self, assignee_id: int) -> int: ...
    def count_queue(self) -> int: ...


@runtime_checkable
class RequestLogRepository(Protocol):
    def add(self, log: RequestLog) -> RequestLog: ...
    def list_for_request(self, request_id: int) -> list[RequestLog]: ...
