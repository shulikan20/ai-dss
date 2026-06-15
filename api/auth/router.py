from __future__ import annotations
import os
import time
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
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

_LOGIN_MAX_FAILURES: int = int(os.environ.get("AUTH_LOGIN_MAX_FAILURES", "10"))
_LOGIN_WINDOW_SEC: int = int(os.environ.get("AUTH_LOGIN_WINDOW_SEC", "300"))
_LOGIN_FAILURES: dict[str, list[float]] = {}


def _login_recent_failures(ip: str) -> list[float]:
    now = time.time()
    fresh = [t for t in _LOGIN_FAILURES.get(ip, []) if now - t < _LOGIN_WINDOW_SEC]
    _LOGIN_FAILURES[ip] = fresh
    return fresh


def _login_is_locked(ip: str) -> bool:
    return len(_login_recent_failures(ip)) >= _LOGIN_MAX_FAILURES


def _login_record_failure(ip: str) -> None:
    _login_recent_failures(ip).append(time.time())


def _login_clear(ip: str) -> None:
    _LOGIN_FAILURES.pop(ip, None)

class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    marketing_opt_in: bool = False


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
    marketing_opt_in: bool = False
    language_preference: str = "en"
    created_at: str

    @classmethod
    def from_user(cls, user) -> "UserResponse":
        return cls(
            id=str(user.id),
            email=user.email,
            email_verified=user.email_verified,
            is_admin=user.is_admin,
            marketing_opt_in=getattr(user, "marketing_opt_in", False),
            language_preference=getattr(user, "language_preference", "en") or "en",
            created_at=user.created_at.isoformat(),
        )


class UpdateMeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    language_preference: str | None = Field(default=None, max_length=5)
    marketing_opt_in: bool | None = None


class AuthResponse(TokenResponse):
    user: UserResponse

@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
def register(
    body: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
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
            marketing_opt_in=body.marketing_opt_in,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    tokens = _create_token_pair(user, db)

    return AuthResponse(
        **tokens.model_dump(),
        user=UserResponse.from_user(user),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Authenticate and get tokens",
)
def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    client_ip = request.client.host if request.client else "unknown"

    if _login_is_locked(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
        )

    user_repo = UserRepository(db)
    user = user_repo.get_user_by_email(body.email)
    _credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None:
        hash_password("dummy-password-for-timing")
        _login_record_failure(client_ip)
        raise _credentials_error

    if not verify_password(body.password, user.password_hash):
        _login_record_failure(client_ip)
        raise _credentials_error
    _login_clear(client_ip)

    tokens = _create_token_pair(user, db)

    return AuthResponse(
        **tokens.model_dump(),
        user=UserResponse.from_user(user),
    )

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
    return UserResponse.from_user(user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update profile preferences (language, marketing opt-in)",
)
def update_me(
    body: UpdateMeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    from api.constants import SUPPORTED_LOCALES

    if body.language_preference is not None:
        if body.language_preference not in SUPPORTED_LOCALES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Unsupported language '{body.language_preference}'. "
                    f"Supported: {', '.join(SUPPORTED_LOCALES)}."
                ),
            )
        user.language_preference = body.language_preference

    if body.marketing_opt_in is not None:
        user.marketing_opt_in = body.marketing_opt_in

    db.flush()
    return UserResponse.from_user(user)


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
