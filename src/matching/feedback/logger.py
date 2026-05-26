from __future__ import annotations
import logging
import uuid
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class FeedbackLogger:
    def __init__(self, db: Session) -> None:
        from api.database.repository import FeedbackRepository
        self._repo = FeedbackRepository(db)

    def log(
        self,
        recommendation_id: uuid.UUID,
        capability_id: str,
        rating: int,
        *,
        was_implemented: bool | None = None,
        comment: str | None = None,
    ) -> None:
        record = self._repo.save(
            recommendation_id=recommendation_id,
            capability_id=capability_id,
            rating=rating,
            was_implemented=was_implemented,
            comment=comment,
        )
        logger.info(
            "Feedback logged: rec=%s cap=%s rating=%d → id=%s",
            str(recommendation_id)[:8],
            capability_id,
            rating,
            str(record.feedback_id)[:8],
        )
