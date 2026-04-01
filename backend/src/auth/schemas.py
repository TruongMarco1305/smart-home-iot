from pydantic import BaseModel, EmailStr, Field
from src.models.user import Role


# --- Request schemas ----------------------------------------------------------

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


# --- Response schemas ---------------------------------------------------------

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    """Safe user representation returned to clients (no password hash)."""
    id: str
    username: str
    email: EmailStr
    role: Role
    is_active: bool


# --- JWT payload (internal) ---------------------------------------------------

class TokenPayload(BaseModel):
    sub: str          # user _id as string
    username: str
    role: Role
