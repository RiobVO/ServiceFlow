"""Общие схемы API: Pagination envelope, ETag-утилиты."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Единый envelope для списочных ответов."""

    items: List[T] = Field(..., description="Элементы текущей страницы.")
    total: int = Field(..., ge=0, description="Всего элементов по фильтру.")
    limit: int = Field(..., ge=1, description="Размер страницы.")
    offset: int = Field(..., ge=0, description="Смещение от начала.")
    has_next: bool = Field(..., description="Есть ли следующая страница.")

    @classmethod
    def of(cls, items: List[T], *, total: int, limit: int, offset: int) -> Page[T]:
        return cls(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_next=(offset + len(items)) < total,
        )


class ProblemDetails(BaseModel):
    """RFC 7807 Problem Details — описательная схема для OpenAPI."""

    type: str = Field(..., examples=["https://serviceflow.local/errors/missing_api_key"])
    title: str = Field(..., examples=["Unauthorized"])
    status: int = Field(..., examples=[401])
    detail: str = Field(..., examples=["Требуется API-ключ в заголовке X-API-Key."])
    instance: str = Field(..., examples=["/api/v1/requests"])
    code: str = Field(..., examples=["missing_api_key"])
    request_id: str | None = Field(None, examples=["2bc8b8d6682048eeab539a149da00210"])
    errors: list[dict] | dict | None = None


# Готовый responses-словарь для переиспользования в роутах.
COMMON_ERROR_RESPONSES = {
    400: {"model": ProblemDetails, "description": "Нарушение бизнес-правила."},
    401: {"model": ProblemDetails, "description": "Требуется аутентификация."},
    403: {"model": ProblemDetails, "description": "Нет прав на действие."},
    404: {"model": ProblemDetails, "description": "Ресурс не найден."},
    409: {"model": ProblemDetails, "description": "Конфликт состояния."},
    412: {"model": ProblemDetails, "description": "Precondition failed (ETag mismatch)."},
    422: {"model": ProblemDetails, "description": "Ошибка валидации тела запроса."},
    429: {"model": ProblemDetails, "description": "Превышен лимит запросов."},
}


def compute_etag(resource_id: int | str, updated_at: datetime, *extra: object) -> str:
    """Детерминированный strong ETag для ресурса.

    Основа — пара (id, updated_at). extra позволяет добавить версию
    при будущем переходе на explicit version column.
    """
    basis = f"{resource_id}:{updated_at.isoformat()}"
    for item in extra:
        basis += f":{item}"
    digest = sha256(basis.encode("utf-8")).hexdigest()[:32]
    return f'"{digest}"'
