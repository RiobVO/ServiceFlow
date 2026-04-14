"""Конечный автомат статусов сервисной заявки.

Сюда вынесена единственная каноническая модель переходов статусов.
Модуль не знает ни про SQLAlchemy, ни про HTTP — его можно гонять
юнит-тестами без внешних зависимостей.

Допустимые переходы:
    NEW         → IN_PROGRESS | CANCELED
    IN_PROGRESS → DONE
    DONE        → (terminal)
    CANCELED    → (terminal)

Дополнительные инварианты:
    - В IN_PROGRESS нельзя попасть без назначенного исполнителя.
    - Нельзя ставить тот же статус, что уже установлен.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.core.enums import RequestStatus
from app.core.exceptions import (
    InProgressRequiresAssignee,
    InvalidStatusTransition,
    StatusAlreadySet,
    StatusIsTerminal,
)

ALLOWED_TRANSITIONS: Mapping[RequestStatus, frozenset[RequestStatus]] = {
    RequestStatus.NEW: frozenset({RequestStatus.IN_PROGRESS, RequestStatus.CANCELED}),
    RequestStatus.IN_PROGRESS: frozenset({RequestStatus.DONE}),
    RequestStatus.DONE: frozenset(),
    RequestStatus.CANCELED: frozenset(),
}

TERMINAL_STATUSES: frozenset[RequestStatus] = frozenset(
    {RequestStatus.DONE, RequestStatus.CANCELED}
)


@dataclass(frozen=True, slots=True)
class TransitionRequest:
    """Чистый DTO на вход FSM — не знает про ORM."""

    current_status: RequestStatus
    target_status: RequestStatus
    current_assignee_id: int | None
    new_assignee_id: int | None  # None == «не менять»


def is_terminal(status: RequestStatus) -> bool:
    return status in TERMINAL_STATUSES


def validate_transition(req: TransitionRequest) -> None:
    """Проверяет валидность перехода. Исключение = отказ.

    Возврат None означает, что переход разрешён — сервис может применить.
    """
    current = req.current_status
    target = req.target_status

    if is_terminal(current):
        raise StatusIsTerminal()

    if target == current:
        raise StatusAlreadySet()

    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidStatusTransition(
            f"Переход {current.value} → {target.value} запрещён.",
            details={"from": current.value, "to": target.value},
        )

    if target == RequestStatus.IN_PROGRESS:
        final_assignee = (
            req.new_assignee_id
            if req.new_assignee_id is not None
            else req.current_assignee_id
        )
        if final_assignee is None:
            raise InProgressRequiresAssignee()
