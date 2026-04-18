"""Health-эндпоинты для kubernetes-style probes.

/health/live:
    Liveness — процесс жив и готов принимать трафик. Не трогает БД,
    т.к. kill-и перезагрузка пода из-за временной недоступности БД
    только усугубляют инцидент.

/health/ready:
    Readiness — зависимости (БД) доступны, трафик можно отправлять.
    Пода исключают из балансировщика, пока readiness не вернётся.

/health (алиас /health/live):
    Обратная совместимость для уже настроенных пробников.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.health import check_database

router = APIRouter(tags=["health"])


@router.get("/health/live", operation_id="health_live", summary="Liveness probe")
def live():
    return {"status": "ok"}


@router.get("/health", operation_id="health_legacy", summary="Alias для /health/live")
def health():
    return {"status": "ok"}


@router.get("/health/ready", operation_id="health_ready", summary="Readiness probe")
def ready():
    db_ok = check_database()
    if db_ok:
        return {"status": "ok", "database": "ok"}
    return JSONResponse(
        status_code=503,
        content={"status": "degraded", "database": "unavailable"},
    )
