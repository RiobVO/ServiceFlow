from http import HTTPStatus

from fastapi.testclient import TestClient


def test_health_ok(client: TestClient):
    """
    Проверяем, что сервис живой и /health отвечает 200.
    """
    resp = client.get("/health")
    assert resp.status_code == HTTPStatus.OK

    data = resp.json()
    # Если у тебя другое поле/формат — подправишь здесь
    assert "status" in data
    # Можно так, если возвращаешь {"status": "ok"}
    # assert data["status"] == "ok"

def test_create_user_without_api_key_unauthorized(client: TestClient):
    """
    Без X-API-Key при POST /users должен быть 401.
    (после того, как админ уже существует)
    """
    resp = client.post(
        "/users",
        json={
            "full_name": "Кто-то без ключа",
            "email": "no_api_key@example.com",
        },
    )

    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    body = resp.json()
    assert body.get("error") == "missing_api_key"
    # Можно дополнительно проверить message:
    assert "API-ключ" in body.get("message", "")


def test_create_user_with_invalid_api_key_unauthorized(client: TestClient):
    """
    Мусорный X-API-Key должен приводить к 401/403 (зависит от твоей реализации).
    Главное — не 201 и не 200.
    """
    resp = client.post(
        "/users",
        headers={"X-API-Key": "this_is_trash_key"},
        json={
            "full_name": "Кто-то с мусорным ключом",
            "email": "trash_key@example.com",
        },
    )

    # Если get_current_user кидает 401 — будет UNAUTHORIZED,
    # если ты сделал 403 — подправишь здесь.
    assert resp.status_code in (
        HTTPStatus.UNAUTHORIZED,
        HTTPStatus.FORBIDDEN,
    )


def test_employee_can_create_service_request(
    client: TestClient,
    employee_api_key: str,
):
    """
    EMPLOYEE со своим api_key создаёт сервисную заявку.
    Ожидаем 201 и корректное тело.
    """

    # TODO: ПОДСТАВЬ свои реальные поля и URL
    # Пример, если у тебя роут /service-requests и поля title + description:
    payload = {
        "title": "Проблема с компьютером",
        "description": "Не включается, чёрный экран",
        # сюда добавь остальные обязательные поля, если они есть
    }

    resp = client.post(
        "/requests",
        headers={"X-API-Key": employee_api_key},
        json=payload,
    )

    from http import HTTPStatus as _HS
    assert resp.status_code == _HS.CREATED

    data = resp.json()
    # Минимальные ожидания, не привязанные к конкретной модели
    assert "id" in data
    # Если есть public_id — можно добавить:
    # assert "public_id" in data
    # Проверка, что то, что мы отправили, отразилось в ответе
    assert data.get("title") == payload["title"]
    assert data.get("description") == payload["description"]
