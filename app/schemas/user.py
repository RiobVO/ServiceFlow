from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, field_validator

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


class UserCreated(UserRead):
    api_key: str


class UserRoleUpdate(BaseModel):
    role: UserRole
