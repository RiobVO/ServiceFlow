import os
import time

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.session import engine


def check_database() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


def wait_for_database() -> None:
    timeout = float(os.getenv("DB_WAIT_TIMEOUT", "10"))
    interval = float(os.getenv("DB_WAIT_INTERVAL", "0.5"))

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if check_database():
            return
        time.sleep(interval)

    raise RuntimeError("Database is not ready (timeout).")
