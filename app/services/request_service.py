"""Сервисный слой заявок.

Работает через Unit of Work: сервис не знает про Session, коммит один
на бизнес-операцию. Все проверки переходов делегированы в
app.domain.request_state_machine.
"""

from __future__ import annotations

from datetime import datetime

from app.core.enums import RequestAction, RequestStatus, UserRole
from app.core.exceptions import (
    AssigneeNotFound,
    PermissionDenied,
    RequestNotFound,
)
from app.core.metrics import requests_created_total, requests_status_changed_total
from app.domain.request_state_machine import (
    TransitionRequest,
    validate_transition,
)
from app.models.outbox import OutboxEvent
from app.models.request import ServiceRequest
from app.models.request_log import RequestLog
from app.models.user import User
from app.schemas.common import Page
from app.schemas.request import RequestCreate, RequestRead, RequestStatusUpdate
from app.uow import SqlAlchemyUnitOfWork


class RequestService:
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    # ---------- создание ----------

    def create(self, data: RequestCreate, current_user: User) -> ServiceRequest:
        if data.assignee_id is not None and self._uow.users.get(data.assignee_id) is None:
            raise AssigneeNotFound()

        if current_user.role == UserRole.EMPLOYEE and data.assignee_id is not None:
            raise PermissionDenied(
                "EMPLOYEE не может назначать исполнителя при создании заявки.",
                code="employee_cannot_assign_on_create",
            )

        req = self._uow.requests.add(
            ServiceRequest(
                title=data.title,
                description=data.description,
                created_by_user_id=current_user.id,
                assigned_to_user_id=data.assignee_id,
            )
        )
        self._uow.request_logs.add(
            RequestLog(
                request_id=req.id,
                user_id=current_user.id,
                action=RequestAction.CREATED.value,
                source="API",
            )
        )
        self._uow.outbox.add(
            OutboxEvent(
                event_type="request.created",
                payload={
                    "request_id": req.id,
                    "created_by_user_id": current_user.id,
                    "assigned_to_user_id": req.assigned_to_user_id,
                    "title": req.title,
                },
            )
        )
        self._uow.commit()
        self._uow.refresh(req)
        requests_created_total.inc()
        return req

    # ---------- чтение ----------

    def get_or_404(self, request_id: int) -> ServiceRequest:
        req = self._uow.requests.get(request_id)
        if req is None:
            raise RequestNotFound()
        return req

    def _page(
        self, items: list[ServiceRequest], total: int, limit: int, offset: int
    ) -> Page[RequestRead]:
        return Page.of(
            [RequestRead.model_validate(r) for r in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    def list(
        self,
        *,
        status: RequestStatus | None = None,
        created_by_id: int | None = None,
        assigned_to_id: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Page[RequestRead]:
        items = self._uow.requests.list(
            status=status,
            created_by_id=created_by_id,
            assigned_to_id=assigned_to_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )
        total = self._uow.requests.count(
            status=status,
            created_by_id=created_by_id,
            assigned_to_id=assigned_to_id,
            date_from=date_from,
            date_to=date_to,
        )
        return self._page(items, total, limit, offset)

    def list_for_creator(self, creator_id: int, *, limit: int, offset: int) -> Page[RequestRead]:
        items = self._uow.requests.list_by_creator(creator_id, limit=limit, offset=offset)
        total = self._uow.requests.count_by_creator(creator_id)
        return self._page(items, total, limit, offset)

    def list_for_assignee(self, assignee_id: int, *, limit: int, offset: int) -> Page[RequestRead]:
        items = self._uow.requests.list_by_assignee(assignee_id, limit=limit, offset=offset)
        total = self._uow.requests.count_by_assignee(assignee_id)
        return self._page(items, total, limit, offset)

    def list_queue(self, *, limit: int, offset: int) -> Page[RequestRead]:
        items = self._uow.requests.list_queue(limit=limit, offset=offset)
        total = self._uow.requests.count_queue()
        return self._page(items, total, limit, offset)

    def list_history(self, request_id: int) -> list[RequestLog]:
        return self._uow.request_logs.list_for_request(request_id)

    # ---------- обновление статуса ----------

    def update_status(
        self,
        request_id: int,
        payload: RequestStatusUpdate,
        current_user: User,
        *,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> ServiceRequest:
        req = self._uow.requests.get(request_id)
        if req is None:
            raise RequestNotFound()

        old_status = req.status
        old_assignee = req.assigned_to_user_id

        if payload.status is not None:
            validate_transition(
                TransitionRequest(
                    current_status=old_status,
                    target_status=payload.status,
                    current_assignee_id=old_assignee,
                    new_assignee_id=payload.assignee_id,
                )
            )
            req.status = payload.status

        if payload.assignee_id is not None:
            if self._uow.users.get(payload.assignee_id) is None:
                raise AssigneeNotFound()
            req.assigned_to_user_id = payload.assignee_id

        req.updated_at = datetime.utcnow()

        # Аудит — в той же транзакции (одна атомарная запись).
        if payload.status is not None and req.status != old_status:
            self._uow.request_logs.add(
                RequestLog(
                    request_id=req.id,
                    user_id=current_user.id,
                    action=RequestAction.STATUS_CHANGED.value,
                    old_value=old_status.value
                    if isinstance(old_status, RequestStatus)
                    else str(old_status),
                    new_value=req.status.value
                    if isinstance(req.status, RequestStatus)
                    else str(req.status),
                    client_ip=client_ip,
                    user_agent=user_agent,
                    comment=payload.comment,
                    source="API",
                )
            )

        if payload.assignee_id is not None and req.assigned_to_user_id != old_assignee:
            self._uow.request_logs.add(
                RequestLog(
                    request_id=req.id,
                    user_id=current_user.id,
                    action=RequestAction.ASSIGNEE_CHANGED.value,
                    old_value=str(old_assignee) if old_assignee is not None else None,
                    new_value=(
                        str(req.assigned_to_user_id)
                        if req.assigned_to_user_id is not None
                        else None
                    ),
                    client_ip=client_ip,
                    user_agent=user_agent,
                    source="API",
                )
            )
            self._uow.outbox.add(
                OutboxEvent(
                    event_type="request.assigned",
                    payload={
                        "request_id": req.id,
                        "old_assignee_id": old_assignee,
                        "new_assignee_id": req.assigned_to_user_id,
                        "actor_id": current_user.id,
                    },
                )
            )

        if payload.status is not None and req.status != old_status:
            self._uow.outbox.add(
                OutboxEvent(
                    event_type="request.status_changed",
                    payload={
                        "request_id": req.id,
                        "from": old_status.value
                        if isinstance(old_status, RequestStatus)
                        else str(old_status),
                        "to": req.status.value
                        if isinstance(req.status, RequestStatus)
                        else str(req.status),
                        "actor_id": current_user.id,
                    },
                )
            )

        self._uow.commit()
        self._uow.refresh(req)
        if payload.status is not None and req.status != old_status:
            requests_status_changed_total.labels(
                from_status=old_status.value
                if isinstance(old_status, RequestStatus)
                else str(old_status),
                to_status=req.status.value
                if isinstance(req.status, RequestStatus)
                else str(req.status),
            ).inc()
        return req
