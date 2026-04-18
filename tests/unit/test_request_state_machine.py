"""Юнит-тесты доменного FSM. Без БД, без HTTP."""

from __future__ import annotations

import pytest

from app.core.enums import RequestStatus
from app.core.exceptions import (
    InProgressRequiresAssignee,
    InvalidStatusTransition,
    StatusAlreadySet,
    StatusIsTerminal,
)
from app.domain.request_state_machine import (
    TransitionRequest,
    is_terminal,
    validate_transition,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "target",
    [RequestStatus.IN_PROGRESS, RequestStatus.CANCELED],
)
def test_new_can_transition_to_in_progress_or_canceled(target):
    req = TransitionRequest(
        current_status=RequestStatus.NEW,
        target_status=target,
        current_assignee_id=42 if target == RequestStatus.IN_PROGRESS else None,
        new_assignee_id=None,
    )
    validate_transition(req)


def test_in_progress_requires_assignee():
    req = TransitionRequest(
        current_status=RequestStatus.NEW,
        target_status=RequestStatus.IN_PROGRESS,
        current_assignee_id=None,
        new_assignee_id=None,
    )
    with pytest.raises(InProgressRequiresAssignee):
        validate_transition(req)


def test_same_status_rejected():
    req = TransitionRequest(
        current_status=RequestStatus.NEW,
        target_status=RequestStatus.NEW,
        current_assignee_id=None,
        new_assignee_id=None,
    )
    with pytest.raises(StatusAlreadySet):
        validate_transition(req)


@pytest.mark.parametrize("current", [RequestStatus.DONE, RequestStatus.CANCELED])
def test_terminal_blocks_any_transition(current):
    req = TransitionRequest(
        current_status=current,
        target_status=RequestStatus.IN_PROGRESS,
        current_assignee_id=1,
        new_assignee_id=None,
    )
    with pytest.raises(StatusIsTerminal):
        validate_transition(req)


def test_illegal_transition_new_to_done():
    req = TransitionRequest(
        current_status=RequestStatus.NEW,
        target_status=RequestStatus.DONE,
        current_assignee_id=1,
        new_assignee_id=None,
    )
    with pytest.raises(InvalidStatusTransition):
        validate_transition(req)


def test_is_terminal():
    assert is_terminal(RequestStatus.DONE)
    assert is_terminal(RequestStatus.CANCELED)
    assert not is_terminal(RequestStatus.NEW)
    assert not is_terminal(RequestStatus.IN_PROGRESS)


def test_in_progress_accepts_new_assignee_in_payload():
    req = TransitionRequest(
        current_status=RequestStatus.NEW,
        target_status=RequestStatus.IN_PROGRESS,
        current_assignee_id=None,
        new_assignee_id=7,
    )
    # Не должно упасть — финальный assignee возьмётся из payload.
    validate_transition(req)
