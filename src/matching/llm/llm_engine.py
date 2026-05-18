from __future__ import annotations
import dataclasses
import requests

from src.catalog.repository import CatalogRepository
from src.matching.base import BaseMatchEngine
from src.matching.filters.domain_filter import apply_domain_filter
from src.matching.filters.feasibility_filter import apply_feasibility_filter
from src.matching.llm.extractor import OllamaExtractor
from src.models.company_profile import CompanyProfile
from src.models.recommendation import (
    ClassicalResult,
    DimensionBreakdown,
    LLMResult,
)

class LLMEngine(BaseMatchEngine):
    def __init__(
        self,
        repo: CatalogRepository,
        extractor: OllamaExtractor | None = None,
    ):
        self._repo = repo
        self._extractor = extractor or OllamaExtractor()

    def name(self) -> str:
        return "llm"

    @classmethod
    def build(cls, repo: CatalogRepository) -> LLMEngine:
        return cls(repo=repo, extractor=OllamaExtractor())

    def _get_scoped_capabilities(self, profile: CompanyProfile):
        all_caps = self._repo.get_capabilities()
        passed, _ = apply_feasibility_filter(profile, all_caps, self._repo)
        return apply_domain_filter(profile, passed)

    def extract(self, profile: CompanyProfile) -> LLMResult:
        scoped = self._get_scoped_capabilities(profile)
        if not scoped:
            return LLMResult(
                ranked_items=[],
                cot_reasoning="No capabilities passed filters.",
                model_used=self._extractor._model,
            )
        return self._extractor.extract(profile, scoped)

    def match(self, profile: CompanyProfile) -> list[ClassicalResult]:
        try:
            llm_result = self.extract(profile)
        except requests.exceptions.ConnectionError:
            import warnings
            warnings.warn(
                "LLMEngine: Ollama is not running. "
                "Start it with: ollama serve",
                RuntimeWarning,
                stacklevel=2,
            )
            return []

        return self._to_classical_results(llm_result)

    @staticmethod
    def _to_classical_results(llm_result: LLMResult) -> list[ClassicalResult]:
        items = llm_result.ranked_items
        if not items:
            return []

        n = len(items)
        empty_dims = DimensionBreakdown(
            semantic_fit=0.0,
            integration_compat=0.0,
            data_readiness=0.0,
            tech_fit=0.0,
            pain_point_match=0.0,
        )

        return [
            ClassicalResult(
                rank=item.rank,
                capability_id=item.capability_id,
                capability_name=item.capability_name,
                domain=item.domain,
                topsis_score=round(1.0 / item.rank, 4),
                dimensions=empty_dims,
                explanation=item.explanation,
                impl_complexity=None,
            )
            for item in items
        ]