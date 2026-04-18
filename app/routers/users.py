"""HTTP-роутер пользователей."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header, Request, status

from app.core.config import settings
from app.core.deps import get_uow
from app.core.enums import UserRole
from app.core.exceptions import (
    DomainError,
    MissingApiKey,
    PermissionDenied,
)
from app.core.rate_limit import limiter
from app.core.security import (
    api_key_scheme,
    get_current_user,
    require_admin,
)
from app.models.user import User
from app.schemas.common import COMMON_ERROR_RESPONSES, Page
from app.schemas.user import (
    ApiKeyRotated,
    UserCreate,
    UserCreated,
    UserRead,
    UserRoleUpdate,
)
from app.services.user_service import UserService, UserWithRawKey
from app.uow import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/users", tags=["users"])


class _BootstrapNotConfigured(DomainError):
    code = "admin_bootstrap_key_not_configured"
    http_status = 500
    default_message = "ADMIN_BOOTSTRAP_KEY не настроен на сервере."


class _InvalidBootstrapKey(PermissionDenied):
    code = "invalid_bootstrap_key"
    default_message = "Некорректный X-Bootstrap-Key."


def get_user_service(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> UserService:
    return UserService(uow)


def _issued_to_response(issued: UserWithRawKey) -> UserCreated:
    u = issued.user
    return UserCreated(
        id=u.id,
        full_name=u.full_name,
        email=u.email,
        is_active=u.is_active,
        role=u.role,
        created_at=u.created_at,
        api_key_last4=u.api_key_last4,
        api_key=issued.raw_api_key,
    )


@router.post(
    "",
    response_model=UserCreated,
    status_code=status.HTTP_201_CREATED,
    operation_id="users_create",
    summary="Создать пользователя (bootstrap / ADMIN)",
    responses={**COMMON_ERROR_RESPONSES},
)
@limiter.limit("5/minute")
def api_create_user(
    request: Request,
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
    api_key: Optional[str] = Depends(api_key_scheme),
    bootstrap_key: Optional[str] = Header(default=None, alias="X-Bootstrap-Key"),
):
    """Создание пользователя.

    Bootstrap: при отсутствии ADMIN в системе принимаем X-Bootstrap-Key
    и создаём первого администратора. В штатном режиме — только ADMIN.
    """
    if not service.has_admin_users():
        expected = settings.admin_bootstrap_key
        if not expected:
            raise _BootstrapNotConfigured()
        if bootstrap_key != expected:
            raise _InvalidBootstrapKey()
        return _issued_to_response(service.create(payload, force_role=UserRole.ADMIN))

    if api_key is None:
        raise MissingApiKey()

    # Штатный режим — только действующий ADMIN.
    # Аутентификация вручную внутри того же UoW, чтобы не плодить Session.
    service.authenticate_admin(api_key)
    return _issued_to_response(service.create(payload))


@router.post(
    "/me/api-key/rotate",
    response_model=ApiKeyRotated,
    status_code=status.HTTP_200_OK,
    operation_id="users_rotate_own_api_key",
    summary="Ротация собственного API-ключа",
    responses={**COMMON_ERROR_RESPONSES},
)
@limiter.limit("3/hour")
def api_rotate_own_api_key(
    request: Request,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    issued = service.rotate_api_key(current_user.id)
    return ApiKeyRotated(
        api_key=issued.raw_api_key,
        api_key_last4=issued.user.api_key_last4,
    )


@router.post(
    "/{user_id}/api-key/rotate",
    response_model=ApiKeyRotated,
    status_code=status.HTTP_200_OK,
    operation_id="users_admin_rotate_api_key",
    summary="ADMIN: ротация ключа произвольного пользователя",
    responses={**COMMON_ERROR_RESPONSES},
)
@limiter.limit("10/hour")
def api_admin_rotate_api_key(
    request: Request,
    user_id: int,
    service: UserService = Depends(get_user_service),
    _: User = Depends(require_admin),
):
    issued = service.rotate_api_key(user_id)
    return ApiKeyRotated(
        api_key=issued.raw_api_key,
        api_key_last4=issued.user.api_key_last4,
    )


@router.get(
    "",
    response_model=Page[UserRead],
    operation_id="users_list",
    summary="Список пользователей (ADMIN)",
    responses={**COMMON_ERROR_RESPONSES},
)
def api_list_users(
    service: UserService = Depends(get_user_service),
    _: User = Depends(require_admin),
    limit: int = 50,
    offset: int = 0,
):
    return service.list(limit=limit, offset=offset)


@router.get(
    "/me",
    response_model=UserRead,
    operation_id="users_me",
    summary="Текущий пользователь",
    responses={**COMMON_ERROR_RESPONSES},
)
def api_get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch(
    "/{user_id}/role",
    response_model=UserRead,
    operation_id="users_update_role",
    summary="Сменить роль пользователя (ADMIN)",
    responses={**COMMON_ERROR_RESPONSES},
)
def api_update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    service: UserService = Depends(get_user_service),
    _: User = Depends(require_admin),
):
    return service.update_role(user_id, payload.role)
