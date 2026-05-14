from __future__ import annotations

from src.matching.base import BaseMatchEngine
from src.models.company_profile import CompanyProfile
from src.models.recommendation import ClassicalResult

class HybridEngine(BaseMatchEngine):
    def name(self) -> str:
        return "hybrid"

    def match(self, profile: CompanyProfile) -> list[ClassicalResult]:
        raise NotImplementedError("HybridEngine not implemented.")