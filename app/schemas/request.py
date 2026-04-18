from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator, UUID4

from app.core.enums import RequestStatus


class RequestCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = Field(None, max_length=2000)
    assignee_id: int | None = Field(None, ge=1)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            # кастомный текст, который увидишь в pydantic-ошибке
            raise ValueError("title_cannot_be_empty")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        # если строка только из пробелов — считаем, что описания нет
        return v or None


class RequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    public_id: UUID4

    title: str
    description: str | None = None
    status: RequestStatus
    created_by_user_id: int
    assigned_to_user_id: int | None = None
    created_at: datetime
    updated_at: datetime



class RequestStatusUpdate(BaseModel):
    status: RequestStatus
    assignee_id: int | None = Field(default=None, ge=1)
    comment: str | None = Field(
        default=None,
        max_length=500,
        description="Комментарий при изменении статуса (обязательно при CANCEL)"
    )


