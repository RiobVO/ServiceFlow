"""Rate limiting.

slowapi хранит счётчики in-memory (процессе uvicorn). Для multi-instance
деплоя нужен shared storage — переключится на Redis-backend сменой
storage_uri. Для одиночного бэкенда/портфолио этого достаточно.

Ключ лимита — IP клиента с учётом заголовков X-Forwarded-For (если
сервис стоит за reverse proxy).
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.logging import get_logger, request_id_ctx

_log = get_logger("ratelimit")


def _client_key(request: Request) -> str:
    # Берём первый адрес из X-Forwarded-For, иначе — адрес соединения.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(
    key_func=_client_key,
    default_limits=["120/minute"],
    headers_enabled=True,  # добавляет X-RateLimit-Limit/Remaining/Reset
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Превращает RateLimitExceeded в Problem Details 429."""
    _log.warning(
        "rate_limit_exceeded",
        path=request.url.path,
        limit=str(exc.detail),
    )
    qs = request.url.query
    instance = f"{request.url.path}?{qs}" if qs else request.url.path
    payload = {
        "type": "https://serviceflow.local/errors/rate_limit_exceeded",
        "title": "Too Many Requests",
        "status": 429,
        "detail": f"Превышен лимит запросов: {exc.detail}.",
        "instance": instance,
        "code": "rate_limit_exceeded",
    }
    rid = request_id_ctx.get()
    if rid:
        payload["request_id"] = rid

    response = JSONResponse(
        status_code=429,
        content=payload,
        media_type="application/problem+json",
    )
    # slowapi умеет считать Retry-After; если доступен — пробрасываем.
    retry_after = getattr(exc, "retry_after", None)
    if retry_after is not None:
        response.headers["Retry-After"] = str(retry_after)
    return response
