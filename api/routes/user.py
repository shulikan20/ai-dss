from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.auth.dependencies import get_current_user
from api.database.connection import get_db
from api.database.models import Company, Feedback, QuestionnaireSession, Recommendation, User
from api.database.repository import (
    FeedbackRepository,
    RefreshTokenRepository,
    SessionRepository,
    UserRepository,
)

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

class RecommendationHistoryResponse(BaseModel):
    total: int
    items: list[RecommendationHistoryItem]

class DataExportResponse(BaseModel):
    user: dict
    companies: list[dict]
    sessions: list[dict]
    feedback: list[dict]
    exported_at: str

class DeleteResponse(BaseModel):
    detail: str

@router.get(
    "/me/recommendations",
    response_model=RecommendationHistoryResponse,
    summary="Recommendation history for the authenticated user",
)
def get_recommendation_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecommendationHistoryResponse:
    user_repo = UserRepository(db)
    session_repo = SessionRepository(db)

    companies = (
        db.query(Company)
        .filter_by(user_id=user.id)
        .all()
    )

    items: list[RecommendationHistoryItem] = []
    for company in companies:
        records = session_repo.get_by_company(company.id)
        for rec in records:
            snapshot = rec.profile_snapshot or {}
            items.append(
                RecommendationHistoryItem(
                    session_id=str(rec.session_id),
                    recommendation_id=str(rec.recommendation_id),
                    tier=rec.tier,
                    pipeline_used=rec.pipeline_used,
                    llm_available=rec.llm_available,
                    processing_time_ms=rec.processing_time_ms,
                    created_at=rec.created_at.isoformat(),
                    company_name=snapshot.get("company_name"),
                    country=snapshot.get("country"),
                    domains=snapshot.get("active_domains", []),
                )
            )

    items.sort(key=lambda x: x.created_at, reverse=True)

    return RecommendationHistoryResponse(total=len(items), items=items)


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

    for company in companies:
        sessions = (
            db.query(QuestionnaireSession)
            .filter(QuestionnaireSession.company_id == company.id)
            .all()
        )
        for session in sessions:
            recs = (
                db.query(Recommendation)
                .filter(Recommendation.session_id == session.id)
                .all()
            )
            for rec in recs:
                sessions_data.append({
                    "session_id": str(session.id),
                    "recommendation_id": str(rec.id),
                    "company_name": company.company_name,
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

                fbs = (
                    db.query(Feedback)
                    .filter(Feedback.recommendation_id == rec.id)
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
