from __future__ import annotations

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_liveness(client: TestClient):
    resp = client.get("/health/live")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {"status": "ok"}


def test_readiness(client: TestClient):
    resp = client.get("/health/ready")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["database"] == "ok"


def test_create_user_without_api_key_returns_problem_details(client: TestClient):
    resp = client.post(
        "/api/v1/users",
        json={"full_name": "no-key", "email": "nokey@example.com"},
    )
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    assert resp.headers["content-type"].startswith("application/problem+json")
    body = resp.json()
    assert body["code"] == "missing_api_key"
    assert body["status"] == 401
    assert "X-Request-ID" in resp.headers
    assert body["request_id"] == resp.headers["X-Request-ID"]


def test_invalid_api_key_rejected(client: TestClient):
    resp = client.post(
        "/api/v1/users",
        headers={"X-API-Key": "definitely-not-a-real-key"},
        json={"full_name": "trash", "email": "trash@example.com"},
    )
    assert resp.status_code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN)
