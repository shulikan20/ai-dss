from __future__ import annotations

from src.models.recommendation import ClassicalResult, HybridResult, LLMResult

class HybridAggregator:
    def aggregate(
        self,
        classical: list[ClassicalResult],
        llm: LLMResult,
    ) -> HybridResult:
        raise NotImplementedError("HybridAggregator not implemented.")