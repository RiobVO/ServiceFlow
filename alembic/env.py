from logging.config import fileConfig
import os
import sys

from alembic import context
from sqlalchemy import create_engine

# --- Путь к корню проекта (где лежит app/) ---
base_dir = os.path.dirname(os.path.dirname(__file__))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from app.database.base import Base
from app.core.config import settings



# Конфигурация Alembic
config = context.config

# Логирование Alembic (берёт настройки из alembic.ini, но БЕЗ url)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# metadata для автогенерации миграций
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск миграций в 'offline' режиме."""
    url = settings.db_url  # БЕРЁМ URL ИЗ НАСТРОЕК ПРИЛОЖЕНИЯ

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Запуск миграций в 'online' режиме."""
    connectable = create_engine(settings.db_url)  # ТУТ ТОЖЕ settings.db_url

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
