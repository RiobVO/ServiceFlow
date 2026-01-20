from datetime import datetime
from typing import Type

from sqlalchemy.orm import Session

from app.core.enums import UserRole
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.request import RequestCreate, RequestStatusUpdate
from sqlalchemy import desc
from app.models.request import ServiceRequest
from app.core.enums import RequestStatus, RequestAction
from app.services.request_log_service import add_request_log



ALLOWED_TRANSITIONS: dict[RequestStatus, set[RequestStatus]] = {
    RequestStatus.NEW: {RequestStatus.IN_PROGRESS, RequestStatus.CANCELED},
    RequestStatus.IN_PROGRESS: {RequestStatus.DONE},
    RequestStatus.DONE: set(),
    RequestStatus.CANCELED: set(),
}

TERMINAL_STATUSES = {
    RequestStatus.DONE,
    RequestStatus.CANCELED,
}






def create_request(db: Session, data: RequestCreate, current_user: User) -> ServiceRequest:
    # creator теперь берём из текущего пользователя по API-key
    creator = current_user

    if data.assignee_id is not None and db.get(User, data.assignee_id) is None:
        raise ValueError("assignee_not_found")

    # EMPLOYEE не имеет права назначать исполнителя при создании
    if current_user.role == UserRole.EMPLOYEE and data.assignee_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="employee_cannot_assign_on_create",
        )
    req = ServiceRequest(
        title=data.title,
        description=data.description,
        created_by_user_id=creator.id,
        assigned_to_user_id=data.assignee_id,
    )

    db.add(req)
    db.commit()
    db.refresh(req)

    # Логируем факт создания заявки
    add_request_log(
        db=db,
        request_id=req.id,
        user_id=creator.id,
        action=RequestAction.CREATED,
        old_value=None,
        new_value=None,
    )

    return req




def get_request(db: Session, request_id: int):
    return db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()


def list_requests(
    db: Session,
    *,
    status: RequestStatus | None = None,
    created_by_id: int | None = None,
    assigned_to_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ServiceRequest]:
    """
    Список заявок с фильтрами и пагинацией.
    Предполагается, что права доступа проверены на уровне роутера.
    """

    query = db.query(ServiceRequest)

    if status is not None:
        query = query.filter(ServiceRequest.status == status)

    if created_by_id is not None:
        query = query.filter(ServiceRequest.created_by_user_id == created_by_id)

    if assigned_to_id is not None:
        query = query.filter(ServiceRequest.assigned_to_user_id == assigned_to_id)

    if date_from is not None:
        query = query.filter(ServiceRequest.created_at >= date_from)

    if date_to is not None:
        query = query.filter(ServiceRequest.created_at <= date_to)

    query = query.order_by(ServiceRequest.created_at.desc())
    query = query.offset(offset).limit(limit)

    return query.all()



def list_requests_for_creator(
    db: Session,
    creator_id: int,
    limit: int = 50,
    offset: int = 0,
) -> list[Type[ServiceRequest]]:
    return (
        db.query(ServiceRequest)
        .filter(ServiceRequest.created_by_user_id == creator_id)
        .order_by(ServiceRequest.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def list_requests_for_assignee(
    db: Session,
    assignee_id: int,
    limit: int,
    offset: int,
) -> list[Type[ServiceRequest]]:
    return (
        db.query(ServiceRequest)
        .filter(ServiceRequest.assigned_to_user_id == assignee_id)
        .order_by(desc(ServiceRequest.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )


def list_requests_queue(
    db: Session,
    limit: int,
    offset: int,
) -> list[Type[ServiceRequest]]:
    return (
        db.query(ServiceRequest)
        .filter(
            ServiceRequest.status == RequestStatus.NEW,
            ServiceRequest.assigned_to_user_id.is_(None),
        )
        .order_by(desc(ServiceRequest.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )



def update_request_status(db: Session, request_id: int, status: str) -> ServiceRequest:
    req = db.get(ServiceRequest, request_id)
    if not req:
        raise ValueError("request_not_found")

    allowed = {s.value for s in RequestStatus}
    if status not in allowed:
        raise ValueError("invalid_status")

    req.status = status
    req.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(req)
    return req


def update_status(db: Session, request_id: int, payload: RequestStatusUpdate) -> ServiceRequest:
    req = db.get(ServiceRequest, request_id)
    if not req:
        raise ValueError("request_not_found")

    if payload.status is not None:
        current_status = req.status

        if current_status in TERMINAL_STATUSES:
            raise ValueError("status_is_terminal")

        # нельзя ставить тот же статус
        if payload.status == current_status:
            raise ValueError("status_is_already_set")

        if payload.status not in ALLOWED_TRANSITIONS[current_status]:
            raise ValueError(
                f"invalid_status_transition_{current_status}_to_{payload.status}"
            )

        # правило: нельзя IN_PROGRESS без assignee
        if payload.status == RequestStatus.IN_PROGRESS:
            final_assignee = (
                payload.assignee_id
                if payload.assignee_id is not None
                else req.assigned_to_user_id
            )
            if final_assignee is None:
                raise ValueError("in_progress_requires_assignee")

        req.status = payload.status

    # 2) assignee (если передан)
    if payload.assignee_id is not None:
        assignee = db.get(User, payload.assignee_id)
        if not assignee:
            raise ValueError("assignee_not_found")
        req.assigned_to_user_id = payload.assignee_id

    req.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(req)
    return req
