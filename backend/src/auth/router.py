from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.dependencies import get_current_active_user
from src.auth.schemas import LoginRequest, TokenResponse, UserPublic
from src.auth.utils import create_access_token, verify_password
from src.core.database import get_database

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with username & password",
)
async def login(body: LoginRequest):
    """
    Authenticate a user and return a JWT access token.

    - Looks up the user by **username** in MongoDB.
    - Verifies the **bcrypt**-hashed password.
    - Returns a signed JWT containing the user's id, username, and role.
    """
    db = get_database()
    user_doc = await db["users"].find_one({"username": body.username})

    if not user_doc or not verify_password(body.password, user_doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user_doc.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    token = create_access_token(
        user_id=str(user_doc["_id"]),
        username=user_doc["username"],
        role=user_doc["role"],
    )
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get the current authenticated user",
)
async def get_me(current_user: UserPublic = Depends(get_current_active_user)):
    """
    Returns the profile of the currently authenticated user.
    Requires a valid Bearer token in the **Authorization** header.
    """
    return current_user
