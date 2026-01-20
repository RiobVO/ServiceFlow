from app.database.base import Base  # noqa
from app.models.user import User  # noqa: F401
from app.models.request import ServiceRequest  # noqa: F401
from app.models.request_log import RequestLog  # noqa: F401


def init_db() -> None:
    # База теперь поднимается через Alembic-миграции.
    # Функция оставлена для совместимости, но НИЧЕГО не делает.
    pass
