from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.company_profile import CompanyProfile
from src.models.recommendation import ClassicalResult

class BaseMatchEngine(ABC):
    @abstractmethod
    def match(self, profile: CompanyProfile) -> list[ClassicalResult]:
        """Run the full pipeline for a company profile."""

    @abstractmethod
    def name(self) -> str:
        """Short ID "classical", "llm", "hybrid" """