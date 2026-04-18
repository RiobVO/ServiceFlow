from __future__ import annotations

from http import HTTPStatus
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def _email(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:6]}@example.com"


def test_admin_can_create_employee(client: TestClient, admin_api_key: str):
    resp = client.post(
        "/api/v1/users",
        headers={"X-API-Key": admin_api_key},
        json={"full_name": "Иван Иванов", "email": _email("emp")},
    )
    assert resp.status_code == HTTPStatus.CREATED
    body = resp.json()
    assert body["role"] == "employee"
    # Сырой ключ отдаётся один раз и достаточно энтропийный.
    assert isinstance(body["api_key"], str) and len(body["api_key"]) >= 32
    assert body["api_key_last4"] == body["api_key"][-4:]


def test_employee_cannot_create_users(client: TestClient, employee_api_key: str):
    resp = client.post(
        "/api/v1/users",
        headers={"X-API-Key": employee_api_key},
        json={"full_name": "Not allowed", "email": _email("nope")},
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN
    assert resp.json()["code"] == "admin_only"


def test_rotate_own_api_key_invalidates_old(client: TestClient, employee_user):
    old = employee_user.raw_api_key
    resp = client.post(
        "/api/v1/users/me/api-key/rotate",
        headers={"X-API-Key": old},
    )
    assert resp.status_code == HTTPStatus.OK
    new_key = resp.json()["api_key"]
    assert new_key and new_key != old

    # Старый не должен работать
    resp_old = client.get("/api/v1/users/me", headers={"X-API-Key": old})
    assert resp_old.status_code == HTTPStatus.UNAUTHORIZED

    # Новый работает
    resp_new = client.get("/api/v1/users/me", headers={"X-API-Key": new_key})
    assert resp_new.status_code == HTTPStatus.OK


def test_users_list_is_paginated(client: TestClient, admin_api_key: str):
    resp = client.get("/api/v1/users?limit=1&offset=0", headers={"X-API-Key": admin_api_key})
    assert resp.status_code == HTTPStatus.OK
    body = resp.json()
    assert set(body.keys()) == {"items", "total", "limit", "offset", "has_next"}
    assert body["limit"] == 1
    assert body["total"] >= 1
