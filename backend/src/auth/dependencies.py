from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from src.auth.schemas import UserPublic
from src.auth.utils import decode_access_token
from src.core.database import get_database
from src.models.user import Role

_bearer_scheme = HTTPBearer()

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> UserPublic:
    """
    Decode the Bearer JWT and return the corresponding user from MongoDB.
    Raises 401 if the token is missing, expired, or invalid.
    """
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise _CREDENTIALS_EXCEPTION

    db = get_database()
    user_doc = await db["users"].find_one({"username": payload.username})

    if user_doc is None:
        raise _CREDENTIALS_EXCEPTION

    return UserPublic(
        id=str(user_doc["_id"]),
        username=user_doc["username"],
        email=user_doc["email"],
        role=user_doc["role"],
        is_active=user_doc.get("is_active", True),
    )


async def get_current_active_user(
    current_user: UserPublic = Depends(get_current_user),
) -> UserPublic:
    """Extends get_current_user by additionally checking the is_active flag."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    return current_user


def require_roles(*roles: Role) -> Callable:
    """
    Dependency factory for role-based access control.

    Usage::

        @router.delete("/users/{id}", dependencies=[Depends(require_roles(Role.ADMIN))])
        async def delete_user(...): ...
    """
    async def _check(current_user: UserPublic = Depends(get_current_active_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role(s): {[r.value for r in roles]}",
            )
        return current_user

    return _check
