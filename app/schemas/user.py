from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.core.enums import UserRole


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("full_name_too_short")
        if len(v) > 100:
            raise ValueError("full_name_too_long")
        return v


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    role: UserRole
    created_at: datetime
    # Хвост ключа для идентификации в UI: "...abcd". Сам ключ не раскрывается.
    api_key_last4: str | None = None


class UserCreated(UserRead):
    """Специальный вид на UserRead с сырым ключом — отдаётся ОДИН РАЗ."""

    api_key: str


class UserRoleUpdate(BaseModel):
    role: UserRole


class ApiKeyRotated(BaseModel):
    """Результат ротации — показываем сырой ключ один раз."""

    api_key: str
    api_key_last4: str
