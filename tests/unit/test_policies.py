"""Юнит-тесты политик доступа. Без БД."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.enums import RequestStatus, UserRole
from app.core.exceptions import PermissionDenied
from app.policies.request_policy import RequestPolicy
from app.schemas.request import RequestStatusUpdate

pytestmark = pytest.mark.unit


def _user(uid: int, role: UserRole):
    return SimpleNamespace(id=uid, role=role)


def _req(rid: int, *, status=RequestStatus.NEW, created_by=1, assignee=None):
    return SimpleNamespace(
        id=rid,
        status=status,
        created_by_user_id=created_by,
        assigned_to_user_id=assignee,
    )


# ---------- can_view ----------

def test_admin_can_view_any():
    RequestPolicy.can_view(_user(10, UserRole.ADMIN), _req(1, created_by=5))


def test_agent_can_view_any():
    RequestPolicy.can_view(_user(10, UserRole.AGENT), _req(1, created_by=5))


def test_employee_sees_own():
    RequestPolicy.can_view(_user(5, UserRole.EMPLOYEE), _req(1, created_by=5))


def test_employee_blocked_from_foreign():
    with pytest.raises(PermissionDenied):
        RequestPolicy.can_view(_user(99, UserRole.EMPLOYEE), _req(1, created_by=5))


# ---------- can_update_status ----------

def test_agent_cannot_assign_others():
    payload = RequestStatusUpdate(status=RequestStatus.IN_PROGRESS, assignee_id=77)
    with pytest.raises(PermissionDenied) as err:
        RequestPolicy.can_update_status(
            _user(10, UserRole.AGENT), _req(1, assignee=None), payload
        )
    assert err.value.code == "agent_cannot_assign_others"


def test_agent_can_take_from_queue():
    payload = RequestStatusUpdate(status=RequestStatus.IN_PROGRESS, assignee_id=10)
    RequestPolicy.can_update_status(
        _user(10, UserRole.AGENT), _req(1, assignee=None), payload
    )


def test_employee_can_only_cancel_own_new():
    payload = RequestStatusUpdate(status=RequestStatus.CANCELED)
    RequestPolicy.can_update_status(
        _user(5, UserRole.EMPLOYEE),
        _req(1, created_by=5, status=RequestStatus.NEW, assignee=None),
        payload,
    )


def test_employee_cannot_cancel_after_assignment():
    payload = RequestStatusUpdate(status=RequestStatus.CANCELED)
    with pytest.raises(PermissionDenied) as err:
        RequestPolicy.can_update_status(
            _user(5, UserRole.EMPLOYEE),
            _req(1, created_by=5, status=RequestStatus.NEW, assignee=10),
            payload,
        )
    assert err.value.code == "employee_cannot_cancel_after_assignment"
