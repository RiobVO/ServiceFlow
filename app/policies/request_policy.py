from typing import Optional

from fastapi import HTTPException, status

from app.core.enums import UserRole, RequestStatus
from app.models.user import User
from app.models.request import ServiceRequest
from app.schemas.request import RequestStatusUpdate


class RequestPolicy:
    @staticmethod
    def can_view(user: User, request: ServiceRequest) -> None:
        """
        Доступ к одной заявке:
        - ADMIN, AGENT: любую
        - EMPLOYEE: только свои (созданные или назначенные на него)
        """
        if user.role in {UserRole.ADMIN, UserRole.AGENT}:
            return

        if (
            getattr(request, "created_by_user_id", None) == user.id
            or getattr(request, "assigned_to_user_id", None) == user.id
        ):
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="forbidden_to_view_request",
        )

    @staticmethod
    def can_update_status(
        user: User,
        request: ServiceRequest,
        payload: RequestStatusUpdate,
    ) -> None:
        """
        Правила обновления статуса / исполнителя.
        ЛОГИКА 1 В 1 как у тебя была в роутере, только вынесена сюда.
        """

        # ADMIN — может всё, дальше только сервис проверяет корректность переходов
        if user.role == UserRole.ADMIN:
            return

        # AGENT — ограниченный доступ
        if user.role == UserRole.AGENT:
            # 0) Терминальные статусы менять нельзя
            if request.status in {RequestStatus.DONE, RequestStatus.CANCELED}:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="agent_cannot_modify_terminal",
                )

            # 1) Агент не может назначать других пользователей
            if payload.assignee_id is not None and payload.assignee_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="agent_cannot_assign_others",
                )

            # 2) Может брать заявку, если она БЕЗ исполнителя и он назначает себя
            is_taking_from_queue = (
                    getattr(request, "assigned_to_user_id", None) is None
                    and payload.assignee_id == user.id
            )

            # 3) Может модифицировать заявку, только если она принадлежит ему
            is_assigned_to_me = getattr(request, "assigned_to_user_id", None) == user.id

            # 4) Если ни одно из условий не подходит — он не имеет права
            if not is_assigned_to_me and not is_taking_from_queue:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="agent_cannot_modify_foreign_request",
                )

            return

        if user.role == UserRole.EMPLOYEE:
            # 1) Может трогать только заявку, которую сам создал
            if getattr(request, "created_by_user_id", None) != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="employee_cannot_modify_foreign_request",
                )

            # 2) EMPLOYEE никогда не может менять исполнителя
            if payload.assignee_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="employee_cannot_change_assignee",
                )

            # 3) EMPLOYEE может менять статус только на CANCELED
            if payload.status is not None:
                # Разрешён только CANCELED
                if payload.status != RequestStatus.CANCELED:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="employee_cannot_set_status",
                    )

                # И только если заявка ещё не назначена и всё ещё NEW
                if (
                        getattr(request, "assigned_to_user_id", None) is not None
                        or request.status != RequestStatus.NEW
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="employee_cannot_cancel_after_assignment",
                    )

            return

