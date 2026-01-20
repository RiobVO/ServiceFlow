# app/core/security.py

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.user import User
from app.core.enums import UserRole


api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    api_key: str | None = Depends(api_key_scheme),
) -> User:
    """
    Достаём текущего пользователя по API-ключу.

    - если ключ не передан → missing_api_key
    - если ключ не найден в базе → invalid_api_key
    - если пользователь выключен (is_active = False) → user_inactive
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing_api_key",
        )

    user: User | None = db.query(User).filter(User.api_key == api_key).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_api_key",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user_inactive",
        )

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Депенденси для эндпоинтов, доступных только ADMIN.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin_only",
        )
    return current_user


def require_agent_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Депенденси для эндпоинтов, доступных AGENT или ADMIN.
    """
    if current_user.role not in {UserRole.ADMIN, UserRole.AGENT}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="agent_or_admin_only",
        )
    return current_user
