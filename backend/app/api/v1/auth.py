"""
Authentication Endpoints: Google OAuth, Dev Mock Login, Token Refresh, Profile.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ...db.session import get_db
from ...models.user import User
from ...schemas.user import (
    GoogleAuthRequest,
    DevLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    UserUpdateRequest,
)
from ...core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_google_token,
)
from ...core.deps import get_current_user
from ...core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=TokenResponse)
async def login_with_google(
    req: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """Sign in or register using Google OAuth2 ID Token."""
    google_data = verify_google_token(req.id_token)
    if not google_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google OAuth credential token",
        )

    email = google_data["email"]
    google_id = google_data["google_id"]

    stmt = select(User).where((User.email == email) | (User.google_id == google_id))
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        user = User(
            email=email,
            google_id=google_id,
            display_name=google_data.get("name", "Scholar"),
            avatar_url=google_data.get("picture", ""),
            role="user",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        if not user.google_id:
            user.google_id = google_id
        if google_data.get("picture"):
            user.avatar_url = google_data["picture"]
        await db.commit()
        await db.refresh(user)

    token_data = {"sub": user.id, "email": user.email, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/dev-login", response_model=TokenResponse)
async def login_dev(
    req: DevLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Dev Mock login for local development without live Google OAuth credentials."""
    if not settings.ENABLE_DEV_LOGIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev login is disabled in this environment",
        )

    stmt = select(User).where(User.email == req.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        user = User(
            email=req.email,
            display_name=req.display_name or "Scholar Alex",
            avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
            role="user",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token_data = {"sub": user.id, "email": user.email, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh")
async def refresh_access_token(
    req: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate new access token using a valid refresh token."""
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    return {"access_token": new_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    user: User = Depends(get_current_user),
):
    """Get authenticated user profile."""
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    req: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update profile information for the authenticated user."""
    if req.display_name is not None and req.display_name.strip():
        user.display_name = req.display_name.strip()
    if req.avatar_url is not None:
        user.avatar_url = req.avatar_url
    if req.daily_goal is not None:
        if req.daily_goal < 1 or req.daily_goal > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Daily goal must be between 1 and 500 cards.",
            )
        user.daily_goal = req.daily_goal
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/dev-users", response_model=List[UserResponse])
async def list_dev_users(
    db: AsyncSession = Depends(get_db),
):
    """List sample users for quick multi-account switching when DEV mode is active."""
    if not settings.ENABLE_DEV_LOGIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev mode is disabled in production",
        )
    stmt = select(User).limit(10)
    res = await db.execute(stmt)
    users = res.scalars().all()
    return [UserResponse.model_validate(u) for u in users]
