from __future__ import annotations
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.auth.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from api.auth.dependencies import get_current_user
from api.database.connection import get_db
from api.database.models import User
from api.database.repository import RefreshTokenRepository, UserRepository

router = APIRouter()

class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60

class UserResponse(BaseModel):
    id: str
    email: str
    email_verified: bool
    is_admin: bool
    created_at: str

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
def register(
    body: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user_repo = UserRepository(db)
    existing = user_repo.get_user_by_email(body.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    try:
        user = user_repo.create_user(
            email=body.email,
            password_hash=hash_password(body.password),
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    tokens = _create_token_pair(user, db)
    return tokens


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and get tokens",
)
def login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user_repo = UserRepository(db)
    user = user_repo.get_user_by_email(body.email)
    _credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None:
        hash_password("dummy-password-for-timing")
        raise _credentials_error

    if not verify_password(body.password, user.password_hash):
        raise _credentials_error

    tokens = _create_token_pair(user, db)
    return tokens

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Get new access token using refresh token",
)
def refresh(
    body: RefreshRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    token_repo = RefreshTokenRepository(db)
    token_hash = hash_refresh_token(body.refresh_token)
    stored = token_repo.get_by_hash(token_hash)
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_repo.revoke(token_hash)
    user_repo = UserRepository(db)
    user = user_repo.get_user_by_id(stored.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer active.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = _create_token_pair(user, db)
    return tokens

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke refresh token (logout)",
)
def logout(
    body: RefreshRequest,
    db: Session = Depends(get_db),
) -> None:
    token_repo = RefreshTokenRepository(db)
    token_hash = hash_refresh_token(body.refresh_token)
    token_repo.revoke(token_hash)

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        email_verified=user.email_verified,
        is_admin=user.is_admin,
        created_at=user.created_at.isoformat(),
    )

def _create_token_pair(user: User, db: Session) -> TokenResponse:
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"is_admin": user.is_admin},
    )
    raw_refresh = generate_refresh_token()
    refresh_hash = hash_refresh_token(raw_refresh)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token_repo = RefreshTokenRepository(db)
    token_repo.create(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=expires_at,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
    )
