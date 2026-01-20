import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.user import User
from app.core.enums import UserRole

@pytest.fixture(scope="session")
def db_session():
    """
    Живой Session к той же БД, что использует backend в контейнере.
    Тесты мы будем запускать через `docker compose exec backend pytest`,
    так что хост db будет доступен.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def client():
    """
    FastAPI TestClient — тесты будут дергать эндпоинты прямо через код приложения,
    без HTTP-запросов наружу.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def admin_api_key(db_session):
    """
    Достаём api_key первого ADMIN из БД.
    Будем использовать его в тестах, где нужен доступ администратора.
    """
    admin: User | None = (
        db_session.query(User)
        .filter(User.role == UserRole.ADMIN)
        .order_by(User.id.asc())
        .first()
    )
    assert admin is not None, "В базе нет ADMIN-пользователя — прогоняй bootstrap перед тестами"
    assert admin.api_key, "У админа нет api_key"
    return admin.api_key


@pytest.fixture(scope="session")
def employee_api_key(db_session):
    """
    Берём api_key обычного EMPLOYEE из БД.
    Нужен, чтобы проверять доступы обычного пользователя.
    """
    employee: User | None = (
        db_session.query(User)
        .filter(User.role == UserRole.EMPLOYEE)
        .order_by(User.id.asc())
        .first()
    )
    assert employee is not None, "В базе нет EMPLOYEE-пользователя — сидер должен его создать"
    assert employee.api_key, "У EMPLOYEE нет api_key"
    return employee.api_key