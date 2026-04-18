"""Сидирование базовых пользователей.

Выводит сырые API-ключи в stdout ТОЛЬКО при первом создании —
после этого в БД остаётся только argon2-хеш, и ключ не восстановить.
"""

from __future__ import annotations

from app.core.enums import UserRole
from app.schemas.user import UserCreate
from app.services.user_service import UserService
from app.uow import SqlAlchemyUnitOfWork


def _ensure(service: UserService, *, full_name: str, email: str, role: UserRole) -> None:
    existing = service._uow.users.get_by_email(email)  # noqa: SLF001
    if existing is not None:
        print(
            f"[SKIP] {role.value.upper():8} уже существует: "
            f"id={existing.id}, email={existing.email}, api_key=***{existing.api_key_last4}"
        )
        return

    issued = service.create(
        UserCreate(full_name=full_name, email=email),
        force_role=role,
    )
    print(
        f"[CREATED] {role.value.upper():8} id={issued.user.id}, email={issued.user.email}\n"
        f"          API_KEY (сохрани, второй раз не покажем) = {issued.raw_api_key}\n"
    )


def main() -> None:
    print("===> Старт инициализации пользователей")
    with SqlAlchemyUnitOfWork() as uow:
        service = UserService(uow)
        _ensure(service, full_name="Admin User", email="admin@example.com", role=UserRole.ADMIN)
        _ensure(service, full_name="Support Agent", email="agent@example.com", role=UserRole.AGENT)
        _ensure(service, full_name="Test Employee", email="employee@example.com", role=UserRole.EMPLOYEE)
    print("===> Готово.")


if __name__ == "__main__":
    main()
