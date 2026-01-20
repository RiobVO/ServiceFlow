from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import api_key_scheme, get_current_user, get_db, require_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserCreated, UserRead, UserRoleUpdate
from app.services.user_service import (
    create_user,
    has_admin_users,
    list_users,
    update_user_role,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserCreated, status_code=status.HTTP_201_CREATED)
def api_create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    api_key: Optional[str] = Depends(api_key_scheme),
    bootstrap_key: Optional[str] = Header(default=None, alias="X-Bootstrap-Key"),
):
    """
    Создание пользователя.

    Первый ADMIN:
    - в системе ещё нет админов
    - передан корректный X-Bootstrap-Key == ADMIN_BOOTSTRAP_KEY

    После появления первого ADMIN:
    - создавать пользователей может только авторизованный ADMIN
    """
    admin_exists = (
            db.query(User)
            .filter(User.role == UserRole.ADMIN)
            .first()
            is not None
    )

    # 1) Админов ещё нет → bootstrap-режим
    if not admin_exists:
        if not settings.ADMIN_BOOTSTRAP_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="admin_bootstrap_key_not_configured",
            )

        if bootstrap_key != settings.ADMIN_BOOTSTRAP_KEY:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="invalid_bootstrap_key",
            )

        # создаём ПЕРВОГО АДМИНА
        user = create_user(db, payload, force_role=UserRole.ADMIN)
        return user

    # 2) Админ уже есть → любой POST /users только через ADMIN
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing_api_key",
        )

    current_user = get_current_user(db=db, api_key=api_key)
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin_only",
        )

    try:
        user = create_user(db, payload)
    except ValueError as exc:
        if str(exc) == "email_already_exists":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="email_already_exists",
            )
        raise

    return user


@router.get("", response_model=List[UserRead])
def api_list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    limit: int = 50,
    offset: int = 0,
):
    return list_users(db, limit=limit, offset=offset)


@router.get("/me", response_model=UserRead)
def api_get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/{user_id}/role", response_model=UserRead)
def api_update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        user = update_user_role(db, user_id, payload.role)
    except ValueError as exc:
        if str(exc) == "user_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="user_not_found",
            )
        raise
    return user
