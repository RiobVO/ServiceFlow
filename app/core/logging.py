"""Структурное логирование через structlog.

JSON-вывод в stdout, обогащение контекстом через contextvars:
    - request_id — сквозной идентификатор запроса
    - user_id    — идентификатор аутентифицированного пользователя (если есть)
    - method, path, status_code — заполняются access-логом middleware

Стандартный logging-модуль мостируется в structlog, чтобы логи
uvicorn/sqlalchemy попадали в тот же pipeline.
"""

from __future__ import annotations

import logging
import os
import sys
from contextvars import ContextVar
from typing import Any

import structlog

# Сквозные переменные запроса
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_ctx: ContextVar[int | None] = ContextVar("user_id", default=None)


def _add_request_context(_logger: Any, _method: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    rid = request_id_ctx.get()
    uid = user_id_ctx.get()
    if rid is not None:
        event_dict.setdefault("request_id", rid)
    if uid is not None:
        event_dict.setdefault("user_id", uid)
    return event_dict


def configure_logging(level: str | None = None, *, json_logs: bool | None = None) -> None:
    """Настраивает structlog + stdlib logging.

    level:     уровень логирования (ENV LOG_LEVEL, по умолчанию INFO)
    json_logs: JSON (prod) или человекочитаемый (dev) вывод.
               ENV LOG_JSON=1/0, по умолчанию True.
    """
    level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    if json_logs is None:
        json_logs = os.getenv("LOG_JSON", "1") != "0"

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        _add_request_context,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        timestamper,
    ]

    if json_logs:
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level)),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Мостим stdlib → structlog, чтобы uvicorn/sqlalchemy шли в тот же renderer.
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Приглушаем слишком болтливые логгеры
    for noisy in ("uvicorn.access",):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.stdlib.get_logger(name)
