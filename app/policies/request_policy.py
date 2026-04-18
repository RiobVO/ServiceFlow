"""Политики доступа к заявкам.

Policy не знает про HTTP. Любое нарушение — исключение из core.exceptions,
которое ляжет в Problem Details глобальным хендлером.
"""

from __future__ import annotations

from app.core.enums import RequestStatus, UserRole
from app.core.exceptions import PermissionDenied
from app.models.request import ServiceRequest
from app.models.user import User
from app.schemas.request import RequestStatusUpdate


class RequestPolicy:
    @staticmethod
    def can_view(user: User, request: ServiceRequest) -> None:
        if user.role in {UserRole.ADMIN, UserRole.AGENT}:
            return

        if request.created_by_user_id == user.id or request.assigned_to_user_id == user.id:
            return

        raise PermissionDenied(
            "Нет прав на просмотр заявки.",
            code="forbidden_to_view_request",
        )

    @staticmethod
    def can_view_history(user: User, request: ServiceRequest) -> None:
        if user.role in {UserRole.ADMIN, UserRole.AGENT}:
            return

        if request.created_by_user_id == user.id or request.assigned_to_user_id == user.id:
            return

        raise PermissionDenied(
            "Нет прав на просмотр истории заявки.",
            code="forbidden_to_view_history",
        )

    @staticmethod
    def can_update_status(
        user: User,
        request: ServiceRequest,
        payload: RequestStatusUpdate,
    ) -> None:
        if user.role == UserRole.ADMIN:
            return

        if user.role == UserRole.AGENT:
            _check_agent_update(user, request, payload)
            return

        if user.role == UserRole.EMPLOYEE:
            _check_employee_update(user, request, payload)
            return


def _check_agent_update(
    user: User, request: ServiceRequest, payload: RequestStatusUpdate
) -> None:
    # Терминальные статусы AGENT менять не может.
    if request.status in {RequestStatus.DONE, RequestStatus.CANCELED}:
        raise PermissionDenied(
            "AGENT не может менять заявку в терминальном статусе.",
            code="agent_cannot_modify_terminal",
        )

    # Назначать можно только себя.
    if payload.assignee_id is not None and payload.assignee_id != user.id:
        raise PermissionDenied(
            "AGENT может назначать только себя.",
            code="agent_cannot_assign_others",
        )

    is_taking_from_queue = (
        request.assigned_to_user_id is None and payload.assignee_id == user.id
    )
    is_assigned_to_me = request.assigned_to_user_id == user.id

    if not is_assigned_to_me and not is_taking_from_queue:
        raise PermissionDenied(
            "AGENT не может модифицировать чужую заявку.",
            code="agent_cannot_modify_foreign_request",
        )


def _check_employee_update(
    user: User, request: ServiceRequest, payload: RequestStatusUpdate
) -> None:
    if request.created_by_user_id != user.id:
        raise PermissionDenied(
            "EMPLOYEE может менять только свои заявки.",
            code="employee_cannot_modify_foreign_request",
        )

    if payload.assignee_id is not None:
        raise PermissionDenied(
            "EMPLOYEE не может менять исполнителя.",
            code="employee_cannot_change_assignee",
        )

    if payload.status is not None:
        if payload.status != RequestStatus.CANCELED:
            raise PermissionDenied(
                "EMPLOYEE может только отменить свою заявку.",
                code="employee_cannot_set_status",
            )

        if request.assigned_to_user_id is not None or request.status != RequestStatus.NEW:
            raise PermissionDenied(
                "EMPLOYEE не может отменить заявку после назначения.",
                code="employee_cannot_cancel_after_assignment",
            )
