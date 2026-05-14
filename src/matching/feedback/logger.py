from __future__ import annotations

from src.models.company_profile import CompanyProfile
from src.models.recommendation import HybridResult

class FeedbackLogger:
    def log(self, profile: CompanyProfile, result: HybridResult, rating: int) -> None:
        raise NotImplementedError("FeedbackLogger does not work in this version.")