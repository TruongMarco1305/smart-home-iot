from typing import Literal
from pydantic import BaseModel, EmailStr, Field
from src.models.user import Role


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Role = Role.VIEWER


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6)
