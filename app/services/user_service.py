"""Сервисный слой пользователей (через UoW)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.core.enums import UserRole
from app.core.exceptions import (
    AdminOnly,
    EmailAlreadyExists,
    InvalidApiKey,
    UserInactive,
    UserNotFound,
)
from app.core.hashing import (
    extract_prefix,
    generate_api_key,
    hash_api_key,
    needs_rehash,
    verify_api_key,
)
from app.core.metrics import api_key_auth_total
from app.models.user import User
from app.schemas.common import Page
from app.schemas.user import UserCreate, UserRead
from app.uow import SqlAlchemyUnitOfWork


@dataclass(frozen=True, slots=True)
class UserWithRawKey:
    """Результат операции, где нужно отдать клиенту сырой API-ключ."""

    user: User
    raw_api_key: str


class UserService:
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    def has_admin_users(self) -> bool:
        return self._uow.users.any_admin()

    def create(
        self,
        payload: UserCreate,
        force_role: Optional[UserRole] = None,
    ) -> UserWithRawKey:
        if self._uow.users.get_by_email(payload.email) is not None:
            raise EmailAlreadyExists()

        role = force_role if force_role is not None else UserRole.EMPLOYEE
        issued = generate_api_key()

        user = self._uow.users.add(
            User(
                full_name=payload.full_name.strip(),
                email=str(payload.email).lower(),
                is_active=True,
                role=role,
                api_key_prefix=issued.prefix,
                api_key_last4=issued.last4,
                api_key_hash=issued.hash,
            )
        )
        self._uow.commit()
        self._uow.refresh(user)
        return UserWithRawKey(user=user, raw_api_key=issued.raw)

    def rotate_api_key(self, user_id: int) -> UserWithRawKey:
        user = self._uow.users.get(user_id)
        if user is None:
            raise UserNotFound()

        issued = generate_api_key()
        user.api_key_prefix = issued.prefix
        user.api_key_last4 = issued.last4
        user.api_key_hash = issued.hash
        self._uow.commit()
        self._uow.refresh(user)
        return UserWithRawKey(user=user, raw_api_key=issued.raw)

    def list(self, *, limit: int = 50, offset: int = 0) -> Page[UserRead]:
        items = self._uow.users.list(limit=limit, offset=offset)
        total = self._uow.users.count()
        return Page.of(
            [UserRead.model_validate(u) for u in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    def authenticate(self, raw_api_key: str) -> User:
        """Аутентификация по сырому ключу. Выбрасывает доменные ошибки."""
        prefix = extract_prefix(raw_api_key)
        for user in self._uow.users.get_by_api_key_prefix(prefix):
            if verify_api_key(raw_api_key, user.api_key_hash):
                if needs_rehash(user.api_key_hash):
                    user.api_key_hash = hash_api_key(raw_api_key)
                    self._uow.commit()
                if not user.is_active:
                    api_key_auth_total.labels(result="inactive").inc()
                    raise UserInactive()
                api_key_auth_total.labels(result="ok").inc()
                return user
        api_key_auth_total.labels(result="invalid").inc()
        raise InvalidApiKey()

    def authenticate_admin(self, raw_api_key: str) -> User:
        user = self.authenticate(raw_api_key)
        if user.role != UserRole.ADMIN:
            raise AdminOnly()
        return user

    def update_role(self, user_id: int, role: UserRole) -> User:
        user = self._uow.users.get(user_id)
        if user is None:
            raise UserNotFound()
        user.role = role
        self._uow.commit()
        self._uow.refresh(user)
        return user
