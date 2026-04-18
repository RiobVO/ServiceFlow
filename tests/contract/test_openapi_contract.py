"""Schemathesis: property-based проверки контракта на основе OpenAPI.

Цель: ни один из сгенерированных запросов не должен приводить к 500
и не должен ломать инварианты Problem Details на ошибках.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.contract]

schemathesis = pytest.importorskip("schemathesis")


@pytest.fixture(scope="module")
def schema(_app_with_db):
    # Загружаем OpenAPI прямо из приложения.
    return schemathesis.openapi.from_asgi("/openapi.json", _app_with_db)


@pytest.fixture(scope="module")
def _seed_admin(_app_with_db):
    """Сид: один админ, чей ключ будет прикреплён ко всем запросам schemathesis."""
    from uuid import uuid4

    from app.core.enums import UserRole
    from app.schemas.user import UserCreate
    from app.services.user_service import UserService
    from app.uow import SqlAlchemyUnitOfWork

    with SqlAlchemyUnitOfWork() as uow:
        service = UserService(uow)
        return service.create(
            UserCreate(
                full_name="Schemathesis Admin",
                email=f"st_admin_{uuid4().hex[:6]}@example.com",
            ),
            force_role=UserRole.ADMIN,
        )


@pytest.fixture
def case_hook(_seed_admin):
    """Проставляем валидный X-API-Key на каждый сгенерированный запрос."""

    def _hook(case):
        case.headers = dict(case.headers or {})
        case.headers["X-API-Key"] = _seed_admin.raw_api_key
        return case

    return _hook


# По умолчанию schemathesis прогоняет все операции. Ограничим количество примеров,
# чтобы прогон был детерминированным и быстрым.
@pytest.mark.usefixtures("_seed_admin")
def test_api_does_not_500(schema, case_hook):
    @schema.parametrize()
    def check(case):
        case = case_hook(case)
        response = case.call()
        # Никаких 500 — всё должно быть либо осмысленным ответом, либо
        # Problem Details с корректным статусом и content-type.
        assert (
            response.status_code < 500
        ), f"Got {response.status_code} on {case.method} {case.path}: {response.text}"
        if response.status_code >= 400 and response.headers.get("content-type", "").startswith(
            "application/problem+json"
        ):
            body = response.json()
            for field in ("type", "title", "status", "detail", "instance", "code"):
                assert field in body, f"missing {field} in problem details: {body}"

    check()
