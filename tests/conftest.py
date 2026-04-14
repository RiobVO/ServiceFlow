"""Корневой conftest.

- Для unit-тестов БД не нужна — они скипают integration-фикстуры.
- Для integration/contract используем testcontainers: на session-scope
  поднимаем postgres, накатываем alembic, передаём всем тестам TestClient,
  переопределив engine и SessionLocal.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from uuid import uuid4

import pytest


# --------------------- общие утилиты ---------------------


def _unique_email(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}@example.com"


# --------------------- инфраструктура Postgres ---------------------


@pytest.fixture(scope="session")
def _postgres_url() -> Iterator[str]:
    """Поднимает postgres-контейнер и возвращает DSN.

    Если выставлена переменная DATABASE_URL_POSTGRES — используем её
    (быстрый локальный прогон без docker-socket'а).
    """
    external = os.getenv("DATABASE_URL_POSTGRES")
    if external:
        yield external
        return

    from testcontainers.postgres import PostgresContainer

    with PostgresContainer(
        image="postgres:16-alpine",
        username="test",
        password="test",
        dbname="serviceflow_test",
    ) as pg:
        url = pg.get_connection_url().replace("postgresql+psycopg2://", "postgresql+psycopg://")
        os.environ["DATABASE_URL_POSTGRES"] = url
        os.environ.setdefault("ADMIN_BOOTSTRAP_KEY", "test_admin_bootstrap_key_long_enough")
        yield url


@pytest.fixture(scope="session")
def _app_with_db(_postgres_url: str):
    """Применяет миграции и возвращает FastAPI-приложение."""
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", _postgres_url)
    command.upgrade(alembic_cfg, "head")

    from app.main import app

    return app


@pytest.fixture()
def client(_app_with_db):
    """TestClient с полностью настроенным приложением."""
    from fastapi.testclient import TestClient

    with TestClient(_app_with_db) as c:
        yield c


# --------------------- фабрики пользователей ---------------------


@pytest.fixture()
def admin_user(_app_with_db):
    from app.core.enums import UserRole
    from app.schemas.user import UserCreate
    from app.services.user_service import UserService
    from app.uow import SqlAlchemyUnitOfWork

    with SqlAlchemyUnitOfWork() as uow:
        service = UserService(uow)
        return service.create(
            UserCreate(full_name="Admin", email=_unique_email("admin")),
            force_role=UserRole.ADMIN,
        )


@pytest.fixture()
def agent_user(_app_with_db):
    from app.core.enums import UserRole
    from app.schemas.user import UserCreate
    from app.services.user_service import UserService
    from app.uow import SqlAlchemyUnitOfWork

    with SqlAlchemyUnitOfWork() as uow:
        service = UserService(uow)
        return service.create(
            UserCreate(full_name="Agent", email=_unique_email("agent")),
            force_role=UserRole.AGENT,
        )


@pytest.fixture()
def employee_user(_app_with_db):
    from app.core.enums import UserRole
    from app.schemas.user import UserCreate
    from app.services.user_service import UserService
    from app.uow import SqlAlchemyUnitOfWork

    with SqlAlchemyUnitOfWork() as uow:
        service = UserService(uow)
        return service.create(
            UserCreate(full_name="Employee", email=_unique_email("employee")),
            force_role=UserRole.EMPLOYEE,
        )


@pytest.fixture()
def admin_api_key(admin_user) -> str:
    return admin_user.raw_api_key


@pytest.fixture()
def agent_api_key(agent_user) -> str:
    return agent_user.raw_api_key


@pytest.fixture()
def employee_api_key(employee_user) -> str:
    return employee_user.raw_api_key
