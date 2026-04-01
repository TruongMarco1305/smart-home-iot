from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import settings
from src.auth.schemas import TokenPayload
from src.models.user import Role

# --- Password hashing ---------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# --- JWT ----------------------------------------------------------------------

def create_access_token(user_id: str, username: str, role: Role) -> str:
    """Create a signed JWT that expires after ACCESS_TOKEN_EXPIRE_MINUTES."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": user_id,
        "username": username,
        "role": role.value,
        "exp": expire,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT.
    Raises jose.JWTError on any failure (expired, invalid signature, etc.).
    """
    raw = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    return TokenPayload(
        sub=raw["sub"],
        username=raw["username"],
        role=Role(raw["role"]),
    )
