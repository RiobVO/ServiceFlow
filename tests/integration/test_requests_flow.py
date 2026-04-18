"""Интеграционный тест полного флоу заявки: NEW → IN_PROGRESS → DONE + audit."""

from __future__ import annotations

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_full_request_lifecycle(
    client: TestClient,
    admin_user,
    employee_api_key: str,
    admin_api_key: str,
):
    # 1. Employee создаёт заявку (c Idempotency-Key)
    create = client.post(
        "/api/v1/requests",
        headers={"X-API-Key": employee_api_key, "Idempotency-Key": "abc-1"},
        json={"title": "Ноутбук не включается", "description": "Чёрный экран"},
    )
    assert create.status_code == HTTPStatus.CREATED
    req = create.json()
    req_id = req["id"]
    assert req["status"] == "NEW"
    assert "ETag" in create.headers

    # 1b. Повтор с тем же ключом и телом — должен вернуть тот же ответ
    repeat = client.post(
        "/api/v1/requests",
        headers={"X-API-Key": employee_api_key, "Idempotency-Key": "abc-1"},
        json={"title": "Ноутбук не включается", "description": "Чёрный экран"},
    )
    assert repeat.status_code == HTTPStatus.CREATED
    assert repeat.json()["id"] == req_id

    # 1c. Тот же ключ с другим телом — 409
    conflict = client.post(
        "/api/v1/requests",
        headers={"X-API-Key": employee_api_key, "Idempotency-Key": "abc-1"},
        json={"title": "Другое", "description": "Совсем"},
    )
    assert conflict.status_code == HTTPStatus.CONFLICT
    assert conflict.json()["code"] == "idempotency_key_conflict"

    # 2. Admin ставит IN_PROGRESS с assignee=себя
    update = client.patch(
        f"/api/v1/requests/{req_id}/status",
        headers={"X-API-Key": admin_api_key},
        json={"status": "IN_PROGRESS", "assignee_id": admin_user.user.id},
    )
    assert update.status_code == HTTPStatus.OK
    assert update.json()["status"] == "IN_PROGRESS"
    etag_after_update = update.headers["ETag"]

    # 3. Admin закрывает DONE, передавая If-Match → проходит
    done = client.patch(
        f"/api/v1/requests/{req_id}/status",
        headers={"X-API-Key": admin_api_key, "If-Match": etag_after_update},
        json={"status": "DONE"},
    )
    assert done.status_code == HTTPStatus.OK
    assert done.json()["status"] == "DONE"

    # 4. Нельзя менять терминальный
    again = client.patch(
        f"/api/v1/requests/{req_id}/status",
        headers={"X-API-Key": admin_api_key},
        json={"status": "IN_PROGRESS"},
    )
    assert again.status_code == HTTPStatus.BAD_REQUEST
    assert again.json()["code"] == "status_is_terminal"

    # 5. История содержит все переходы
    history = client.get(
        f"/api/v1/requests/{req_id}/history",
        headers={"X-API-Key": admin_api_key},
    )
    assert history.status_code == HTTPStatus.OK
    actions = [row["action"] for row in history.json()]
    assert actions.count("created") == 1
    assert actions.count("status_changed") == 2


def test_if_match_mismatch_returns_412(
    client: TestClient,
    admin_user,
    employee_api_key: str,
    admin_api_key: str,
):
    r = client.post(
        "/api/v1/requests",
        headers={"X-API-Key": employee_api_key},
        json={"title": "Что-то", "description": None},
    )
    req_id = r.json()["id"]

    resp = client.patch(
        f"/api/v1/requests/{req_id}/status",
        headers={"X-API-Key": admin_api_key, "If-Match": '"bogus"'},
        json={"status": "IN_PROGRESS", "assignee_id": admin_user.user.id},
    )
    assert resp.status_code == HTTPStatus.PRECONDITION_FAILED
    assert resp.json()["code"] == "optimistic_lock_failed"


def test_invalid_transition_returns_problem_details(
    client: TestClient,
    employee_api_key: str,
    admin_api_key: str,
):
    r = client.post(
        "/api/v1/requests",
        headers={"X-API-Key": employee_api_key},
        json={"title": "X", "description": None},
    )
    req_id = r.json()["id"]

    # NEW → DONE напрямую запрещено
    resp = client.patch(
        f"/api/v1/requests/{req_id}/status",
        headers={"X-API-Key": admin_api_key},
        json={"status": "DONE"},
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.json()["code"] == "invalid_status_transition"


def test_employee_cannot_see_foreign_request(
    client: TestClient,
    admin_user,
    employee_api_key: str,
    admin_api_key: str,
):
    # создаёт admin — employee не должен видеть
    r = client.post(
        "/api/v1/requests",
        headers={"X-API-Key": admin_api_key},
        json={"title": "admin-created", "description": None},
    )
    req_id = r.json()["id"]

    resp = client.get(
        f"/api/v1/requests/{req_id}",
        headers={"X-API-Key": employee_api_key},
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN
    assert resp.json()["code"] == "forbidden_to_view_request"
