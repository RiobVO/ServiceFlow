"""SQLAlchemy engine и Session factory.

Параметры пула подобраны под умеренную нагрузку одиночного бэкенда:
    pool_size=10, max_overflow=10 — суммарно до 20 соединений;
    pool_pre_ping=True — отсеивает мёртвые коннекты после простоя/рестартов БД;
    pool_recycle=1800 — защита от idle-timeout у Postgres/pgbouncer (часто 30–60 мин);
    pool_timeout=10 — быстрый fail вместо длинного ожидания.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.db_url,
    echo=False,
    pool_size=10,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=10,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
