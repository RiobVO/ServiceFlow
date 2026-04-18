"""DI-зависимости FastAPI для доменных сервисов.

Держим здесь, а не в security.py, чтобы security отвечал только за аутентификацию.
"""

from __future__ import annotations

from collections.abc import Iterator

from app.uow import SqlAlchemyUnitOfWork


def get_uow() -> Iterator[SqlAlchemyUnitOfWork]:
    uow = SqlAlchemyUnitOfWork()
    with uow:
        yield uow
