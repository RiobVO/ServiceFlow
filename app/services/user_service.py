from __future__ import annotations

import secrets
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate


def _generate_api_key() -> str:
    # 32 байта случайных данных -> безопасный ключ
    return secrets.token_urlsafe(32)


def has_admin_users(db: Session) -> bool:
    stmt = select(User.id).where(User.role == UserRole.ADMIN).limit(1)
    return db.execute(stmt).first() is not None


def create_user(
    db: Session,
    payload: UserCreate,
    force_role: Optional[UserRole] = None,
) -> User:
    # проверка уникальности email
    existing = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()
    if existing is not None:
        raise ValueError("email_already_exists")

    if force_role is not None:
        role = force_role
    else:
        # по умолчанию обычный сотрудник
        role = UserRole.EMPLOYEE

    user = User(
        full_name=payload.full_name.strip(),
        email=str(payload.email).lower(),
        is_active=True,
        role=role,
        api_key=_generate_api_key(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session, limit: int = 50, offset: int = 0) -> list[User]:
    stmt = select(User).offset(offset).limit(limit)
    return list(db.scalars(stmt).all())

def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def update_user_role(db: Session, user_id: int, role: UserRole) -> User:
    user = db.get(User, user_id)
    if not user:
        raise ValueError("user_not_found")
    user.role = role
    db.commit()
    db.refresh(user)
    return user
