from __future__ import annotations
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.auth.dependencies import get_current_user
from api.constants import DISCLOSURE_TEXT
from api.database.connection import get_db
from api.database.models import Company, Feedback, QuestionnaireSession, Recommendation, User
from api.database.repository import (
    FeedbackRepository,
    RefreshTokenRepository,
    SavedToolRepository,
    SessionRepository,
    UserRepository,
)
from api.models import DimensionBreakdownModel, RecommendationItem
from api.routes.recommend import _MAX_RESULTS, _build_product_list

router = APIRouter()

class RecommendationHistoryItem(BaseModel):
    session_id: str
    recommendation_id: str
    tier: str
    pipeline_used: str
    llm_available: bool
    processing_time_ms: int | None
    created_at: str
    company_name: str | None = None
    country: str | None = None
    domains: list[str] = []
    top_recommendation: str | None = None
    feedback_rating: int | None = None

class RecommendationHistoryResponse(BaseModel):
    total: int
    items: list[RecommendationHistoryItem]

class AssessmentDetailResponse(BaseModel):
    session_id: str
    recommendation_id: str
    company_name: str | None = None
    country: str | None = None
    tier: str
    pipeline_used: str
    llm_available: bool
    processing_time_ms: int | None = None
    created_at: str
    ai_disclosure: str
    recommendations: list[RecommendationItem]

class DataExportResponse(BaseModel):
    user: dict
    companies: list[dict]
    sessions: list[dict]
    feedback: list[dict]
    exported_at: str

class DeleteResponse(BaseModel):
    detail: str

class SavedToolRequest(BaseModel):
    capability_id: str = Field(max_length=100, pattern=r"^[a-z0-9_]+$")
    capability_name: str | None = Field(default=None, max_length=255)

class SavedToolItem(BaseModel):
    capability_id: str
    capability_name: str | None = None
    saved_at: str

class SavedToolListResponse(BaseModel):
    total: int
    items: list[SavedToolItem]

@router.get(
    "/me/recommendations",
    response_model=RecommendationHistoryResponse,
    summary="Recommendation history for the authenticated user",
)
def get_recommendation_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecommendationHistoryResponse:
    rows = (
        db.query(QuestionnaireSession, Recommendation)
        .join(Company, QuestionnaireSession.company_id == Company.id)
        .join(Recommendation, Recommendation.session_id == QuestionnaireSession.id)
        .filter(Company.user_id == user.id)
        .order_by(QuestionnaireSession.created_at.desc())
        .all()
    )

    rec_ids = [rec.id for _, rec in rows]
    rating_map: dict = {}
    if rec_ids:
        fb_rows = (
            db.query(Feedback.recommendation_id, Feedback.rating)
            .filter(
                Feedback.recommendation_id.in_(rec_ids),
                Feedback.rating.isnot(None),
            )
            .order_by(Feedback.created_at.asc())
            .all()
        )
        for fb_rec_id, fb_rating in fb_rows:
            rating_map[fb_rec_id] = fb_rating

    items: list[RecommendationHistoryItem] = []
    for session, rec in rows:
        snapshot = session.profile_snapshot or {}
        ranked = rec.ranked_results or []
        top_rec = (
            ranked[0].get("capability_name")
            if ranked and isinstance(ranked[0], dict)
            else None
        )
        items.append(
            RecommendationHistoryItem(
                session_id=str(session.id),
                recommendation_id=str(rec.id),
                tier=session.tier,
                pipeline_used=rec.pipeline_used,
                llm_available=rec.llm_available,
                processing_time_ms=rec.processing_time_ms,
                created_at=session.created_at.isoformat(),
                company_name=snapshot.get("company_name"),
                country=snapshot.get("country"),
                domains=snapshot.get("active_domains", []),
                top_recommendation=top_rec,
                feedback_rating=rating_map.get(rec.id),
            )
        )

    return RecommendationHistoryResponse(total=len(items), items=items)

@router.get(
    "/me/recommendations/{session_id}",
    response_model=AssessmentDetailResponse,
    summary="Full snapshot of one past assessment (for re-viewing results)",
)
def get_assessment_detail(
    request: Request,
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssessmentDetailResponse:
    found = SessionRepository(db).get_session_with_recommendation_for_user(
        session_id, user.id
    )
    if found is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )
    session, rec = found

    snapshot = session.profile_snapshot or {}
    country = snapshot.get("country") or ""
    catalog_repo = request.app.state.repo

    ranked = sorted(
        (r for r in (rec.ranked_results or []) if isinstance(r, dict)),
        key=lambda r: r.get("rank", 999),
    )[:_MAX_RESULTS]

    items: list[RecommendationItem] = []
    for r in ranked:
        dims = r.get("dimensions") or {}
        products = catalog_repo.get_products(r.get("capability_id", ""))
        items.append(
            RecommendationItem(
                rank=r.get("rank", 0),
                capability_id=r.get("capability_id", ""),
                capability_name=r.get("capability_name", ""),
                domain=r.get("domain", ""),
                topsis_score=round(float(r.get("topsis_score", 0.0)), 4),
                explanation=r.get("explanation") or "",
                dimensions=DimensionBreakdownModel(
                    semantic_fit=round(float(dims.get("semantic_fit", 0.0)), 4),
                    integration_compat=round(float(dims.get("integration_compat", 0.0)), 4),
                    data_readiness=round(float(dims.get("data_readiness", 0.0)), 4),
                    tech_fit=round(float(dims.get("tech_fit", 0.0)), 4),
                    pain_point_match=round(float(dims.get("pain_point_match", 0.0)), 4),
                ),
                products=_build_product_list(products, country=country),
            )
        )

    return AssessmentDetailResponse(
        session_id=str(session.id),
        recommendation_id=str(rec.id),
        company_name=snapshot.get("company_name"),
        country=snapshot.get("country"),
        tier=session.tier,
        pipeline_used=rec.pipeline_used,
        llm_available=rec.llm_available,
        processing_time_ms=rec.processing_time_ms,
        created_at=session.created_at.isoformat(),
        ai_disclosure=DISCLOSURE_TEXT,
        recommendations=items,
    )

@router.delete(
    "/me/recommendations/{session_id}",
    response_model=DeleteResponse,
    summary="Delete one assessment (session + recommendation + feedback)",
)
def delete_assessment(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeleteResponse:
    removed = SessionRepository(db).delete_session_for_user(session_id, user.id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )
    return DeleteResponse(detail="Assessment deleted.")

@router.post(
    "/me/saved-tools",
    response_model=SavedToolItem,
    summary="Bookmark a capability for the authenticated user",
)
def save_tool(
    body: SavedToolRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedToolItem:
    repo = SavedToolRepository(db)
    saved = repo.save(
        user_id=user.id,
        capability_id=body.capability_id,
        capability_name=body.capability_name,
    )
    return SavedToolItem(
        capability_id=saved.capability_id,
        capability_name=saved.capability_name,
        saved_at=saved.saved_at.isoformat(),
    )


@router.get(
    "/me/saved-tools",
    response_model=SavedToolListResponse,
    summary="List the authenticated user's saved tools",
)
def list_saved_tools(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedToolListResponse:
    repo = SavedToolRepository(db)
    records = repo.list_for_user(user.id)
    items = [
        SavedToolItem(
            capability_id=r.capability_id,
            capability_name=r.capability_name,
            saved_at=r.saved_at.isoformat(),
        )
        for r in records
    ]
    return SavedToolListResponse(total=len(items), items=items)

@router.delete(
    "/me/saved-tools/{capability_id}",
    response_model=DeleteResponse,
    summary="Remove a saved tool for the authenticated user",
)
def delete_saved_tool(
    capability_id: str = Path(max_length=100, pattern=r"^[a-z0-9_]+$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeleteResponse:
    repo = SavedToolRepository(db)
    removed = repo.delete(user_id=user.id, capability_id=capability_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No saved tool '{capability_id}' for this user.",
        )
    return DeleteResponse(detail=f"Removed saved tool '{capability_id}'.")

@router.get(
    "/me/export",
    response_model=DataExportResponse,
    summary="Export all user data",
)
def export_user_data(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DataExportResponse:
    user_data = {
        "id": str(user.id),
        "email": user.email,
        "email_verified": user.email_verified,
        "created_at": user.created_at.isoformat(),
    }
    companies = db.query(Company).filter(Company.user_id == user.id).all()
    companies_data = [
        {
            "id": str(c.id),
            "company_name": c.company_name,
            "country": c.country,
            "created_at": c.created_at.isoformat(),
        }
        for c in companies
    ]
    sessions_data = []
    feedback_data = []

    rows = (
        db.query(QuestionnaireSession, Recommendation, Company.company_name)
        .join(Company, QuestionnaireSession.company_id == Company.id)
        .join(Recommendation, Recommendation.session_id == QuestionnaireSession.id)
        .filter(Company.user_id == user.id)
        .all()
    )

    for session, rec, company_name in rows:
        sessions_data.append({
            "session_id": str(session.id),
            "recommendation_id": str(rec.id),
            "company_name": company_name,
            "tier": session.tier,
            "domains": session.domains,
            "bottleneck_text": session.bottleneck_text,
            "answers": session.answers,
            "profile_snapshot": session.profile_snapshot,
            "pipeline_used": rec.pipeline_used,
            "llm_available": rec.llm_available,
            "processing_time_ms": rec.processing_time_ms,
            "ranked_results": rec.ranked_results,
            "created_at": session.created_at.isoformat(),
        })

    rec_ids = [rec.id for _, rec, _ in rows]
    if rec_ids:
        fbs = (
            db.query(Feedback)
            .filter(Feedback.recommendation_id.in_(rec_ids))
            .all()
        )
        for fb in fbs:
            feedback_data.append({
                "feedback_id": str(fb.id),
                "recommendation_id": str(fb.recommendation_id),
                "capability_id": fb.capability_id,
                "rating": fb.rating,
                "comment": fb.comment,
                "was_implemented": fb.was_implemented,
                "created_at": fb.created_at.isoformat(),
            })

    return DataExportResponse(
        user=user_data,
        companies=companies_data,
        sessions=sessions_data,
        feedback=feedback_data,
        exported_at=datetime.now(timezone.utc).isoformat(),
    )


@router.delete(
    "/me",
    response_model=DeleteResponse,
    summary="Delete account",
)
def delete_account(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeleteResponse:
    user_repo = UserRepository(db)
    token_repo = RefreshTokenRepository(db)
    feedback_repo = FeedbackRepository(db)
    rec_ids = user_repo.get_recommendation_ids_for_user(user.id)
    anonymised = feedback_repo.anonymize_for_user(rec_ids)
    revoked = token_repo.revoke_all_for_user(user.id)
    user_repo.soft_delete_user(user.id)

    return DeleteResponse(
        detail="Account deleted. Your data has been anonymised per GDPR Article 17."
    )
