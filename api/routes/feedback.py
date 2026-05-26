from __future__ import annotations
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database.connection import get_db
from api.database.repository import FeedbackRepository, SessionRepository
from api.models import FeedbackRequest, FeedbackResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit feedback for a recommendation",
)
def submit_feedback(
    body: FeedbackRequest,
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    if body.rating is None and body.was_implemented is None:
        raise HTTPException(
            status_code=422,
            detail="At least one of 'rating' or 'was_implemented' must be provided.",
        )

    try:
        rec_uuid = uuid.UUID(body.recommendation_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid recommendation_id format.")

    session_repo = SessionRepository(db)
    rec = session_repo.get_recommendation(rec_uuid)
    if rec is None:
        raise HTTPException(status_code=404, detail="Recommendation not found.")

    feedback_repo = FeedbackRepository(db)
    try:
        record = feedback_repo.save(
            recommendation_id=rec_uuid,
            capability_id=body.capability_id,
            rating=body.rating,
            comment=body.comment,
            was_implemented=body.was_implemented,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    logger.info(
        "feedback: rec=%s cap=%s rating=%s implemented=%s",
        body.recommendation_id[:8],
        body.capability_id,
        body.rating,
        body.was_implemented,
    )

    return FeedbackResponse(
        feedback_id=str(record.feedback_id),
        recommendation_id=str(record.recommendation_id),
        capability_id=record.capability_id,
        rating=record.rating,
        was_implemented=record.was_implemented,
    )
