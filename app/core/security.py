"""Аутентификация и авторизация по API-ключу через UoW."""

from __future__ import annotations

from fastapi import Depends
from fastapi.security import APIKeyHeader

from app.core.deps import get_uow
from app.core.enums import UserRole
from app.core.exceptions import (
    AdminOnly,
    AgentOrAdminOnly,
    InvalidApiKey,
    MissingApiKey,
    UserInactive,
)
from app.core.hashing import (
    extract_prefix,
    hash_api_key,
    needs_rehash,
    verify_api_key,
)
from app.core.logging import get_logger, user_id_ctx
from app.models.user import User
from app.uow import SqlAlchemyUnitOfWork

api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)
_log = get_logger("auth")


def _authenticate(uow: SqlAlchemyUnitOfWork, raw_key: str) -> User | None:
    """Находит пользователя по сырому API-ключу через prefix + argon2.verify."""
    prefix = extract_prefix(raw_key)
    candidates = uow.users.get_by_api_key_prefix(prefix)

    for user in candidates:
        if verify_api_key(raw_key, user.api_key_hash):
            if needs_rehash(user.api_key_hash):
                user.api_key_hash = hash_api_key(raw_key)
                uow.commit()
            return user
    return None


def get_current_user(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    api_key: str | None = Depends(api_key_scheme),
) -> User:
    if not api_key:
        raise MissingApiKey()

    user = _authenticate(uow, api_key)
    if user is None:
        _log.warning("invalid_api_key_attempt")
        raise InvalidApiKey()

    if not user.is_active:
        raise UserInactive()

    user_id_ctx.set(user.id)
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise AdminOnly()
    return current_user


def require_agent_or_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.ADMIN, UserRole.AGENT}:
        raise AgentOrAdminOnly()
    return current_user


# Обратная совместимость: код, которому нужна просто Session (например, роуты,
# ещё не переписанные на UoW).
def get_db():
    from app.database.session import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
