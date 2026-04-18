"""Маппер доменных ошибок в RFC 7807 Problem Details.

Единый формат ответа об ошибке:
{
    "type":     "about:blank" | "https://serviceflow/errors/<code>",
    "title":    "короткое человекочитаемое название",
    "status":   HTTP-код,
    "detail":   "подробное сообщение",
    "instance": "/path/?query",
    "code":     "machine_readable_code",
    "errors":   [...]            # опционально (валидация)
}

Content-Type: application/problem+json.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status as http_status

from app.core.exceptions import DomainError
from app.core.logging import get_logger, request_id_ctx

_log = get_logger("errors")

PROBLEM_CONTENT_TYPE = "application/problem+json"
PROBLEM_TYPE_PREFIX = "https://serviceflow.local/errors/"


def _problem_response(
    *,
    status_code: int,
    code: str,
    detail: str,
    instance: str,
    title: str | None = None,
    errors: Any | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    title = title or HTTPStatus(status_code).phrase
    payload: dict[str, Any] = {
        "type": f"{PROBLEM_TYPE_PREFIX}{code}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": instance,
        "code": code,
    }
    # Проставляем request_id в тело ответа — удобно клиенту для репорта бага.
    rid = request_id_ctx.get()
    if rid:
        payload["request_id"] = rid
    if errors is not None:
        payload["errors"] = errors

    return JSONResponse(
        status_code=status_code,
        content=payload,
        media_type=PROBLEM_CONTENT_TYPE,
        headers=headers,
    )


def _instance_of(request: Request) -> str:
    # path + query, чтобы в логах ошибок был воспроизводимый URL без хоста
    qs = request.url.query
    return f"{request.url.path}?{qs}" if qs else request.url.path


# ------------------------------------------------------------------
# Доменные ошибки
# ------------------------------------------------------------------


async def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    return _problem_response(
        status_code=exc.http_status,
        code=exc.code,
        detail=exc.message,
        instance=_instance_of(request),
        errors=exc.details,
    )


# ------------------------------------------------------------------
# Pydantic 422
# ------------------------------------------------------------------


def _cleanup_pydantic_errors(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for err in errors:
        err = err.copy()
        ctx = err.get("ctx")
        if isinstance(ctx, dict) and "error" in ctx and isinstance(ctx["error"], Exception):
            ctx = {**ctx, "error": str(ctx["error"])}
            err["ctx"] = ctx
        cleaned.append(err)
    return cleaned


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _problem_response(
        status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="validation_error",
        detail="Некорректные данные запроса.",
        instance=_instance_of(request),
        errors=_cleanup_pydantic_errors(list(exc.errors())),
    )


# ------------------------------------------------------------------
# HTTPException (пусть остаётся — используется FastAPI/Starlette внутри)
# ------------------------------------------------------------------


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    headers = getattr(exc, "headers", None)

    if isinstance(detail, dict):
        code = str(detail.get("code", detail.get("error", "http_error")))
        message = str(
            detail.get("message") or detail.get("detail") or HTTPStatus(exc.status_code).phrase
        )
        errors = detail.get("errors") or detail.get("details")
    elif isinstance(detail, str):
        code = detail if detail and " " not in detail else "http_error"
        message = detail or HTTPStatus(exc.status_code).phrase
        errors = None
    else:
        code = "http_error"
        message = HTTPStatus(exc.status_code).phrase
        errors = detail

    return _problem_response(
        status_code=exc.status_code,
        code=code,
        detail=message,
        instance=_instance_of(request),
        errors=errors,
        headers=headers,
    )


# ------------------------------------------------------------------
# Неперехваченные ошибки — 500
# ------------------------------------------------------------------


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Не утекаем стектрейс в ответ — это задача логгера.
    _log.exception(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error_type=type(exc).__name__,
    )
    return _problem_response(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="internal_server_error",
        detail="Внутренняя ошибка сервиса.",
        instance=_instance_of(request),
    )
