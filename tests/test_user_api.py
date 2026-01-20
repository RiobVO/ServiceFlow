from http import HTTPStatus
from uuid import uuid4

from fastapi.testclient import TestClient


def _unique_email(prefix: str) -> str:
    # Делаем уникальный e-mail, чтобы каждый прогон тестов не упирался в UNIQUE-ограничение
    return f"{prefix}_{uuid4().hex[:8]}@example.com"


def test_agent_cannot_create_user(client: TestClient, admin_api_key: str):
    """
    Проверяем, что обычный EMPLOYEE / AGENT не может создавать юзеров.
    Для простоты: сперва создаём нового EMPLOYEE через админа,
    потом пробуем его ключом создать ещё одного юзера — должны получить 403.
    """

    # 1. Админ создаёт нового EMPLOYEE
    emp_email = _unique_email("test_emp")
    create_payload = {
        "full_name": "Тестовый сотрудник",
        "email": emp_email,
    }

    create_resp = client.post(
        "/users",
        headers={"X-API-Key": admin_api_key},
        json=create_payload,
    )
    assert create_resp.status_code == HTTPStatus.CREATED

    created = create_resp.json()
    assert created["full_name"] == create_payload["full_name"]
    assert created["email"] == create_payload["email"]
    assert created["role"] == "employee"
    assert isinstance(created["api_key"], str) and len(created["api_key"]) > 10

    agent_api_key = created["api_key"]

    # 2. Тем же api_key (EMPLOYEE) пробуем создать ещё одного юзера — должно быть 403
    second_email = _unique_email("second_emp")
    resp = client.post(
        "/users",
        headers={"X-API-Key": agent_api_key},
        json={
            "full_name": "Попытка создать ещё одного",
            "email": second_email,
        },
    )

    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_admin_can_create_user(client: TestClient, admin_api_key: str):
    """
    Проверяем, что админ может создавать EMPLOYEE.
    """

    new_email = _unique_email("newuser_via_test")
    payload = {
        "full_name": "Новый юзер через тест",
        "email": new_email,
    }

    resp = client.post(
        "/users",
        headers={"X-API-Key": admin_api_key},
        json=payload,
    )

    assert resp.status_code == HTTPStatus.CREATED
    data = resp.json()
    assert data["full_name"] == payload["full_name"]
    assert data["email"] == payload["email"]
    assert data["role"] == "employee"
    assert isinstance(data["api_key"], str) and len(data["api_key"]) > 10
