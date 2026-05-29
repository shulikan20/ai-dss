from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from api.auth.security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from api.database.connection import get_db
from api.database.repository import OAuthAccountRepository, RefreshTokenRepository

router = APIRouter()

OAUTH_REDIRECT_BASE = os.environ.get("OAUTH_REDIRECT_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
_PROVIDERS: dict[str, dict] = {}

def _load_provider(name: str, authorize_url: str, token_url: str, userinfo_url: str) -> None:
    client_id = os.environ.get(f"{name.upper()}_CLIENT_ID")
    client_secret = os.environ.get(f"{name.upper()}_CLIENT_SECRET")
    if client_id and client_secret:
        _PROVIDERS[name] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "authorize_url": authorize_url,
            "token_url": token_url,
            "userinfo_url": userinfo_url,
        }

_load_provider(
    "google",
    authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
    token_url="https://oauth2.googleapis.com/token",
    userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
)
_load_provider(
    "microsoft",
    authorize_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
    token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
    userinfo_url="https://graph.microsoft.com/v1.0/me",
)
_load_provider(
    "github",
    authorize_url="https://github.com/login/oauth/authorize",
    token_url="https://github.com/login/oauth/access_token",
    userinfo_url="https://api.github.com/user",
)

_pending_states: dict[str, float] = {}
_STATE_TTL = 600

def _cleanup_states() -> None:
    now = datetime.now(timezone.utc).timestamp()
    expired = [k for k, v in _pending_states.items() if now - v > _STATE_TTL]
    for k in expired:
        _pending_states.pop(k, None)

_SCOPES = {
    "google": "openid email profile",
    "microsoft": "openid email profile User.Read",
    "github": "user:email",
}

@router.get(
    "/{provider}/authorize",
    summary="Redirect to OAuth provider",
)
def oauth_authorize(provider: str):
    if provider not in _PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OAuth provider '{provider}' is not configured.",
        )

    config = _PROVIDERS[provider]
    state = secrets.token_urlsafe(32)
    _cleanup_states()
    _pending_states[state] = datetime.now(timezone.utc).timestamp()

    callback_url = f"{OAUTH_REDIRECT_BASE}/api/auth/{provider}/callback"

    params = {
        "client_id": config["client_id"],
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": _SCOPES.get(provider, ""),
        "state": state,
    }

    if provider == "microsoft":
        params["response_mode"] = "query"

    return RedirectResponse(
        url=f"{config['authorize_url']}?{urlencode(params)}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get(
    "/{provider}/callback",
    summary="OAuth callback — exchange code for tokens",
)
def oauth_callback(
    provider: str,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    if error:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/app#error={error}",
            status_code=status.HTTP_302_FOUND,
        )

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code or state.",
        )

    if provider not in _PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OAuth provider '{provider}' is not configured.",
        )

    if state not in _pending_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state.",
        )
    _pending_states.pop(state, None)

    config = _PROVIDERS[provider]
    callback_url = f"{OAUTH_REDIRECT_BASE}/api/auth/{provider}/callback"

    import httpx

    try:
        token_response = httpx.post(
            config["token_url"],
            data={
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "code": code,
                "redirect_uri": callback_url,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )
        token_data = token_response.json()
    except Exception as e:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/app#error=token_exchange_failed",
            status_code=status.HTTP_302_FOUND,
        )

    provider_access_token = token_data.get("access_token")
    if not provider_access_token:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/app#error=no_access_token",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        headers = {"Authorization": f"Bearer {provider_access_token}"}
        if provider == "github":
            headers["Accept"] = "application/vnd.github+json"

        profile_response = httpx.get(
            config["userinfo_url"],
            headers=headers,
            timeout=10,
        )
        profile = profile_response.json()
    except Exception as e:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/app#error=profile_fetch_failed",
            status_code=status.HTTP_302_FOUND,
        )

    provider_user_id, email = _extract_profile(provider, profile, provider_access_token)

    if not provider_user_id:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/app#error=profile_invalid",
            status_code=status.HTTP_302_FOUND,
        )

    oauth_repo = OAuthAccountRepository(db)
    user = oauth_repo.find_or_create_user(
        provider=provider,
        provider_user_id=str(provider_user_id),
        email=email,
    )

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

    db.commit()

    fragment = urlencode({
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "user_id": str(user.id),
        "email": user.email,
        "provider": provider,
    })

    return RedirectResponse(
        url=f"{FRONTEND_URL}/app#{fragment}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get(
    "/providers",
    summary="List enabled OAuth providers",
)
def list_providers():
    return {"providers": list(_PROVIDERS.keys())}

def _extract_profile(
    provider: str, profile: dict, access_token: str
) -> tuple[str | None, str | None]:
    """Extract provider_user_id and email from the provider's profile response."""
    if provider == "google":
        return profile.get("sub"), profile.get("email")

    if provider == "microsoft":
        return profile.get("id"), profile.get("mail") or profile.get("userPrincipalName")

    if provider == "github":
        user_id = profile.get("id")
        email = profile.get("email")

        if not email:
            try:
                import httpx
                resp = httpx.get(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github+json",
                    },
                    timeout=10,
                )
                emails = resp.json()
                if isinstance(emails, list):
                    primary = next((e for e in emails if e.get("primary")), None)
                    email = primary["email"] if primary else emails[0].get("email")
            except Exception:
                pass

        return str(user_id) if user_id else None, email

    return None, None
