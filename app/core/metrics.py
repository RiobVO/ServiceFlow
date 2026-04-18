"""Prometheus-метрики.

Используется prometheus-fastapi-instrumentator для стандартных
HTTP-метрик (RPS, latency-гистограммы, in-flight, по статусам).
Плюс добавлены бизнес-счётчики — их инкрементирует сервисный слой.
"""

from __future__ import annotations

from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_fastapi_instrumentator.metrics import (
    default,
    latency,
    requests,
    response_size,
)

# --- бизнес-счётчики ---

requests_created_total = Counter(
    "serviceflow_requests_created_total",
    "Количество созданных заявок.",
)

requests_status_changed_total = Counter(
    "serviceflow_requests_status_changed_total",
    "Переходы статусов заявок.",
    labelnames=("from_status", "to_status"),
)

api_key_auth_total = Counter(
    "serviceflow_api_key_auth_total",
    "Результаты аутентификации по API-ключу.",
    labelnames=("result",),  # ok | invalid | inactive | missing
)


def build_instrumentator() -> Instrumentator:
    """Строит инструментатор с адекватными HTTP-метриками и исключает служебные URL."""
    inst = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        excluded_handlers=["/health.*", "/metrics"],
        inprogress_name="serviceflow_http_inprogress",
        inprogress_labels=True,
    )
    inst.add(default())
    inst.add(latency())
    inst.add(requests())
    inst.add(response_size())
    return inst
