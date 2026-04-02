from typing import Annotated, Literal
from pydantic import BaseModel, Field, field_validator
from src.models.user import Role


def _validate_email(v: str) -> str:
    """Accept any syntactically valid email including .local / non-public TLDs."""
    import re
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
        raise ValueError("Invalid email address")
    return v.lower()


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)
    role: Role = Role.VIEWER

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return _validate_email(v)


class UserUpdate(BaseModel):
    email: str | None = None
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str | None) -> str | None:
        return _validate_email(v) if v is not None else None
