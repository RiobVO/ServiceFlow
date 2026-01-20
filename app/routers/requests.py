from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from app.services.request_log_service import list_request_logs, add_request_log
from app.policies.request_policy import RequestPolicy
from app.core.enums import RequestAction

from datetime import datetime
from app.core.security import get_current_user, get_db
from app.core.enums import UserRole, RequestStatus
from app.models.user import User
from app.schemas.request import RequestCreate, RequestRead, RequestStatusUpdate
from app.services.request_service import (
    create_request,
    get_request,
    list_requests,
    update_status,
    list_requests_for_creator,
    list_requests_for_assignee,
    list_requests_queue,
)

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post(
    "",
    response_model=RequestRead,
    status_code=status.HTTP_201_CREATED,
)
def api_create_request(
    payload: RequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Создаём новую заявку.
    created_by_user_id берём из current_user.
    """
    return create_request(db, payload, current_user)



@router.get("", response_model=List[RequestRead])
def api_list_requests(
    request_status: RequestStatus | None = Query(
        default=None,
        description="Фильтр по статусу заявки",
    ),
    created_by_id: int | None = Query(
        default=None,
        ge=1,
        description="Фильтр по ID создателя заявки",
    ),
    assigned_to_id: int | None = Query(
        default=None,
        ge=1,
        description="Фильтр по ID исполнителя",
    ),
    date_from: datetime | None = Query(
        default=None,
        description="Фильтр: дата создания c (включительно)",
    ),
    date_to: datetime | None = Query(
        default=None,
        description="Фильтр: дата создания по (включительно)",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Сколько заявок вернуть (пагинация)",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Смещение для пагинации",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Список заявок:
    - ADMIN, AGENT: видят все (с фильтрами)
    - EMPLOYEE: запрещено
    """
    if current_user.role not in {UserRole.ADMIN, UserRole.AGENT}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="forbidden_for_employee",
        )

    return list_requests(
        db,
        status=request_status,
        created_by_id=created_by_id,
        assigned_to_id=assigned_to_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


@router.get("/my", response_model=List[RequestRead])
def api_list_my_requests(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Заявки, созданные текущим пользователем.
    Для всех ролей.
    """
    return list_requests_for_creator(db, current_user.id, limit=limit, offset=offset)


@router.get("/assigned-to-me", response_model=List[RequestRead])
def api_list_assigned_to_me(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Заявки, назначенные на текущего пользователя.
    Для всех ролей.
    """
    return list_requests_for_assignee(db, current_user.id, limit=limit, offset=offset)


@router.get("/queue", response_model=List[RequestRead])
def api_list_queue(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Очередь заявок (обычно без исполнителя).
    Доступно только AGENT и ADMIN.
    """
    if current_user.role not in {UserRole.ADMIN, UserRole.AGENT}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="forbidden_for_employee",
        )

    return list_requests_queue(db, limit=limit, offset=offset)


# ===== ОДНА ЗАЯВКА =====

@router.get("/{request_id}", response_model=RequestRead)
def api_get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Доступ к одной заявке:
    - ADMIN, AGENT: любую
    - EMPLOYEE: только если он её создал или он assignee
    """
    req = get_request(db, request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="request_not_found")

    RequestPolicy.can_view(current_user, req)

    return req


# ===== ОБНОВЛЕНИЕ СТАТУСА / ИСПОЛНИТЕЛЯ =====

@router.patch("/{request_id}/status", response_model=RequestRead)
def api_update_status(
    request_id: int,
    payload: RequestStatusUpdate,
    request: Request,  #
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    """
    Правила:
    - ADMIN:
        * может менять статус и assignee как угодно (правила переходов проверяет сервис)
    - AGENT:
        * видит все заявки
        * не может назначать других агентов/людей — только себя
        * может менять статус, если:
            - заявка назначена на него ИЛИ
            - он берёт её из очереди (assignee_id было None, а в payload -> его id)
    - EMPLOYEE:
        * может менять только свои заявки (created_by_user_id == current_user.id)
        * не может менять assignee
        * по статусу: может только CANCEL своей заявки
    """
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    req = get_request(db, request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="request_not_found")

    # сохраняем старые значения ДО изменения — они нужны для логов
    old_status = req.status
    old_assignee = req.assigned_to_user_id

    # 🔥 Вся логика прав теперь тут
    RequestPolicy.can_update_status(current_user, req, payload)

    # Если policy не уронила 403 — значит можно обновлять
    try:
        updated = update_status(db, request_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    _write_logs_after_update(
        db=db,
        request_id=request_id,
        current_user=current_user,
        old_status=old_status,
        old_assignee=old_assignee,
        updated=updated,
        payload=payload,
        client_ip=client_ip,
        user_agent=user_agent,
    )
    return updated


def _write_logs_after_update(
    db: Session,
    request_id: int,
    current_user: User,
    old_status: RequestStatus,
    old_assignee,
    updated,
    payload: RequestStatusUpdate,
    client_ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    """
    Логирование изменений после обновления заявки.
    """

    # если статус изменился — логируем
    if payload.status is not None and updated.status != old_status:
        old_status_value = (
            old_status.value
            if isinstance(old_status, RequestStatus)
            else str(old_status) if old_status is not None
            else None
        )
        new_status_value = (
            updated.status.value
            if isinstance(updated.status, RequestStatus)
            else str(updated.status)
        )

        add_request_log(
            db=db,
            request_id=request_id,
            user_id=current_user.id,
            action=RequestAction.STATUS_CHANGED,
            old_value=old_status_value,
            new_value=new_status_value,
            client_ip=client_ip,
            user_agent=user_agent,
            comment=payload.comment,   # комментарий при смене статуса
            source="API",
        )

    # если изменился исполнитель — логируем
    if payload.assignee_id is not None and updated.assigned_to_user_id != old_assignee:
        add_request_log(
            db=db,
            request_id=request_id,
            user_id=current_user.id,
            action=RequestAction.ASSIGNEE_CHANGED,
            old_value=str(old_assignee) if old_assignee is not None else None,
            new_value=(
                str(updated.assigned_to_user_id)
                if updated.assigned_to_user_id is not None
                else None
            ),
            client_ip=client_ip,
            user_agent=user_agent,
            comment=None,
            source="API",
        )



@router.get("/{request_id}/history")
def api_request_history(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = get_request(db, request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="request_not_found")

    # ADMIN / AGENT видят историю любых заявок
    if current_user.role in {UserRole.ADMIN, UserRole.AGENT}:
        return list_request_logs(db, request_id)

    # EMPLOYEE видит историю только своих заявок
    if (
        getattr(req, "created_by_user_id", None) == current_user.id
        or getattr(req, "assigned_to_user_id", None) == current_user.id
    ):
        return list_request_logs(db, request_id)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="forbidden_to_view_history",
    )
