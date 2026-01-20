from typing import Any
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status as http_status


# Карта "код ошибки" → сообщение
ERROR_MESSAGES: dict[str, str] = {
    "missing_api_key": "Требуется API-ключ в заголовке X-API-Key.",
    "invalid_api_key": "Неверный или неактивный API-ключ.",
    "admin_only": "Этот эндпоинт доступен только администраторам.",
    "email_already_exists": "Пользователь с таким email уже существует.",
    "user_not_found": "Пользователь не найден.",
    "request_not_found": "Заявка не найдена.",
    "assignee_not_found": "Указанный исполнитель не найден.",
    "invalid_status_transition": "Невалидный переход статуса.",
    "status_is_terminal": "Статус заявки окончательный.",
    "in_progress_requires_assignee": "Для IN_PROGRESS нужен исполнитель.",
    "agent_cannot_assign_others": "Агент не может назначать других.",
    "validation_error": "Некорректные данные запроса.",
    "unknown_error": "Непредвиденная внутренняя ошибка.",
}


def build_error_response(
    *,
    code: str,
    status_code: int,
    message: str | None = None,
    details: Any | None = None,
) -> JSONResponse:
    payload: dict[str, Any] = {
        "error": code,
        "message": message or ERROR_MESSAGES.get(code, "Произошла ошибка."),
        "details": details,  # <-- всегда есть
    }

    return JSONResponse(status_code=status_code, content=payload)


# ------------------------------
# ВАЖНО: чистим ошибки Pydantic 422
# ------------------------------

def cleanup_pydantic_errors(errors: list[dict]) -> list[dict]:
    cleaned = []
    for err in errors:
        err = err.copy()
        ctx = err.get("ctx")
        if isinstance(ctx, dict) and "error" in ctx:
            if isinstance(ctx["error"], Exception):
                ctx["error"] = str(ctx["error"])
            err["ctx"] = ctx
        cleaned.append(err)
    return cleaned


# ------------------------------
# Глобальный хендлер RequestValidationError (422)
# ------------------------------

async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = cleanup_pydantic_errors(exc.errors())
    return build_error_response(
        code="validation_error",
        status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
    )


# ------------------------------
# Глобальный хендлер HTTPException
# ------------------------------

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail

    if isinstance(detail, dict):
        code = detail.get("error", "unknown_error")
        message = detail.get("message")
        details = detail.get("details")
    elif isinstance(detail, str):
        code = detail
        message = None
        details = None
    else:
        code = "unknown_error"
        message = None
        details = detail

    return build_error_response(
        code=code,
        status_code=exc.status_code,
        message=message,
        details=details,
    )

# ------------------------------
# Глобальный хендлер ValueError (бизнес-ошибки из сервисов)
# ------------------------------

async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    # detail может быть строкой, dict, чем угодно — ведём себя так же, как в http_exception_handler
    detail = exc.args[0] if exc.args else "unknown_error"

    if isinstance(detail, dict):
        code = detail.get("error", "unknown_error")
        message = detail.get("message")
        details = detail.get("details", None)
    elif isinstance(detail, str):
        code = detail
        message = None
        details = None
    else:
        code = "unknown_error"
        message = None
        details = detail

    # Для бизнес-ошибок логично использовать 400 (Bad Request)
    return build_error_response(
        code=code,
        status_code=http_status.HTTP_400_BAD_REQUEST,
        message=message,
        details=details,
    )
