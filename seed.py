import secrets

from app.database.session import SessionLocal
from app.core.enums import UserRole


def _create_user_if_not_exists(
    db,
    *,
    full_name: str,
    email: str,
    role: UserRole,
):
    # ВАЖНО: сначала подтягиваем ServiceRequest, чтобы он зарегистрировался в ORM
    from app.models.request import ServiceRequest  # noqa: F401
    from app.models.user import User

    user = db.query(User).filter(User.email == email).first()
    if user:
        print(
            f"[SKIP] {role.value.upper():8} уже существует: "
            f"id={user.id}, email={user.email}, api_key={user.api_key}"
        )
        return user

    api_key = secrets.token_urlsafe(32)

    user = User(
        full_name=full_name,
        email=email,
        role=role,
        api_key=api_key,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    print(
        f"[CREATED] {role.value.upper():8} id={user.id}, email={user.email}\n"
        f"          API_KEY = {user.api_key}\n"
    )
    return user


def main() -> None:
    db = SessionLocal()
    try:
        print("===> Старт инициализации пользователей")
        _create_user_if_not_exists(
            db,
            full_name="Admin User",
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        _create_user_if_not_exists(
            db,
            full_name="Support Agent",
            email="agent@example.com",
            role=UserRole.AGENT,
        )
        _create_user_if_not_exists(
            db,
            full_name="Test Employee",
            email="employee@example.com",
            role=UserRole.EMPLOYEE,
        )
        print("===> Готово.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
