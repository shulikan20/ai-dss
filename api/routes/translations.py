from __future__ import annotations
from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.auth.dependencies import get_current_user_optional
from api.database.connection import get_db
from api.database.models import User
from api.database.repository import TranslationRepository

router = APIRouter()


def _parse_accept_language(header: str | None) -> str | None:
    if not header:
        return None
    first = header.split(",")[0].strip()
    if not first or first == "*":
        return None
    return first.split("-")[0].split(";")[0].strip().lower() or None

class TranslationItem(BaseModel):
    entity_type: str
    entity_id: str
    field: str
    value: str

class TranslationListResponse(BaseModel):
    locale: str
    entity_type: str | None = None
    total: int
    items: list[TranslationItem]

@router.get(
    "/translations",
    response_model=TranslationListResponse,
    summary="List stored translations for a locale",
)
def list_translations(
    locale: str | None = Query(
        default=None, min_length=2, max_length=10, description="e.g. 'de'"
    ),
    entity_type: str | None = Query(
        default=None, max_length=50, description="e.g. 'capability', 'ui'"
    ),
    accept_language: str | None = Header(default=None),
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> TranslationListResponse:
    resolved = (
        locale
        or _parse_accept_language(accept_language)
        or (getattr(user, "language_preference", None) if user else None)
        or "en"
    )
    records = TranslationRepository(db).list_for_locale(
        locale=resolved, entity_type=entity_type
    )
    locale = resolved
    return TranslationListResponse(
        locale=locale,
        entity_type=entity_type,
        total=len(records),
        items=[
            TranslationItem(
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                field=r.field,
                value=r.value,
            )
            for r in records
        ],
    )
