"""HTTP-роутер заявок (v1)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status

from app.core.deps import get_uow
from app.core.enums import RequestStatus, UserRole
from app.core.exceptions import (
    IdempotencyKeyConflict,
    OptimisticLockFailed,
    PermissionDenied,
)
from app.core.idempotency import compute_body_hash, validate_key
from app.core.security import get_current_user
from app.models.idempotency import IdempotencyKey
from app.models.user import User
from app.policies.request_policy import RequestPolicy
from app.schemas.common import COMMON_ERROR_RESPONSES, Page, compute_etag
from app.schemas.request import RequestCreate, RequestRead, RequestStatusUpdate
from app.services.request_service import RequestService
from app.uow import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/requests", tags=["requests"])


class _EmployeeListForbidden(PermissionDenied):
    code = "forbidden_for_employee"
    default_message = "Эндпоинт недоступен для EMPLOYEE."


def _require_agent_or_admin(user: User) -> None:
    if user.role not in {UserRole.ADMIN, UserRole.AGENT}:
        raise _EmployeeListForbidden()


def get_request_service(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> RequestService:
    return RequestService(uow)


@router.post(
    "",
    response_model=RequestRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="requests_create",
    summary="Создать заявку",
    responses={**COMMON_ERROR_RESPONSES},
)
def api_create_request(
    payload: RequestCreate,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    key = validate_key(idempotency_key)
    body_hash = compute_body_hash(payload.model_dump(mode="json")) if key else ""

    if key is not None:
        existing = uow.idempotency.get(
            user_id=current_user.id, method="POST", path="/api/v1/requests", key=key
        )
        if existing is not None:
            if existing.request_hash != body_hash:
                raise IdempotencyKeyConflict()
            # Возвращаем сохранённый ответ в исходном формате.
            response.status_code = existing.response_status
            return existing.response_body

    service = RequestService(uow)
    req = service.create(payload, current_user)
    response.headers["ETag"] = compute_etag(req.id, req.updated_at)

    if key is not None:
        body = RequestRead.model_validate(req).model_dump(mode="json")
        uow.idempotency.add(
            IdempotencyKey(
                key=key,
                user_id=current_user.id,
                method="POST",
                path="/api/v1/requests",
                request_hash=body_hash,
                response_status=201,
                response_body=body,
            )
        )
        uow.commit()

    return req


@router.get(
    "",
    response_model=Page[RequestRead],
    operation_id="requests_list",
    summary="Список заявок (ADMIN/AGENT)",
    responses={**COMMON_ERROR_RESPONSES},
)
def api_list_requests(
    request_status: RequestStatus | None = Query(default=None),
    created_by_id: int | None = Query(default=None, ge=1),
    assigned_to_id: int | None = Query(default=None, ge=1),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: RequestService = Depends(get_request_service),
    current_user: User = Depends(get_current_user),
):
    _require_agent_or_admin(current_user)
    return service.list(
        status=request_status,
        created_by_id=created_by_id,
        assigned_to_id=assigned_to_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/my",
    response_model=Page[RequestRead],
    operation_id="requests_list_my",
    summary="Мои заявки",
    responses={**COMMON_ERROR_RESPONSES},
)
def api_list_my_requests(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: RequestService = Depends(get_request_service),
    current_user: User = Depends(get_current_user),
):
    return service.list_for_creator(current_user.id, limit=limit, offset=offset)


@router.get(
    "/assigned-to-me",
    response_model=Page[RequestRead],
    operation_id="requests_list_assigned",
    summary="Назначенные на меня",
    responses={**COMMON_ERROR_RESPONSES},
)
def api_list_assigned_to_me(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: RequestService = Depends(get_request_service),
    current_user: User = Depends(get_current_user),
):
    return service.list_for_assignee(current_user.id, limit=limit, offset=offset)


@router.get(
    "/queue",
    response_model=Page[RequestRead],
    operation_id="requests_list_queue",
    summary="Очередь (NEW без исполнителя)",
    responses={**COMMON_ERROR_RESPONSES},
)
def api_list_queue(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: RequestService = Depends(get_request_service),
    current_user: User = Depends(get_current_user),
):
    _require_agent_or_admin(current_user)
    return service.list_queue(limit=limit, offset=offset)


@router.get(
    "/{request_id}",
    response_model=RequestRead,
    operation_id="requests_get",
    summary="Получить заявку по id",
    responses={**COMMON_ERROR_RESPONSES},
)
def api_get_request(
    request_id: int,
    response: Response,
    service: RequestService = Depends(get_request_service),
    current_user: User = Depends(get_current_user),
):
    req = service.get_or_404(request_id)
    RequestPolicy.can_view(current_user, req)
    response.headers["ETag"] = compute_etag(req.id, req.updated_at)
    return req


@router.patch(
    "/{request_id}/status",
    response_model=RequestRead,
    operation_id="requests_update_status",
    summary="Обновить статус/исполнителя (поддерживает If-Match)",
    responses={**COMMON_ERROR_RESPONSES},
)
def api_update_status(
    request_id: int,
    payload: RequestStatusUpdate,
    http_request: Request,
    response: Response,
    if_match: str | None = Header(default=None, alias="If-Match"),
    service: RequestService = Depends(get_request_service),
    current_user: User = Depends(get_current_user),
):
    req = service.get_or_404(request_id)
    RequestPolicy.can_update_status(current_user, req, payload)

    # Optimistic concurrency control.
    # Если клиент прислал If-Match — он обязан совпасть с актуальным ETag.
    current_etag = compute_etag(req.id, req.updated_at)
    if if_match is not None and if_match.strip() != current_etag:
        raise OptimisticLockFailed()

    updated = service.update_status(
        request_id,
        payload,
        current_user,
        client_ip=http_request.client.host if http_request.client else None,
        user_agent=http_request.headers.get("user-agent"),
    )
    response.headers["ETag"] = compute_etag(updated.id, updated.updated_at)
    return updated


@router.get(
    "/{request_id}/history",
    operation_id="requests_history",
    summary="История изменений заявки",
    responses={**COMMON_ERROR_RESPONSES},
)
def api_request_history(
    request_id: int,
    service: RequestService = Depends(get_request_service),
    current_user: User = Depends(get_current_user),
):
    req = service.get_or_404(request_id)
    RequestPolicy.can_view_history(current_user, req)
    return service.list_history(request_id)
