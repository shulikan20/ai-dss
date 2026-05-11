from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

@dataclass
class DimensionBreakdown:
    semantic_fit: float = 0.0
    integration_compat: float = 0.0
    data_readiness: float = 0.0
    tech_fit: float = 0.0
    pain_point_match: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return {
            "semantic_fit": self.semantic_fit,
            "integration_compat": self.integration_compat,
            "data_readiness": self.data_readiness,
            "tech_fit": self.tech_fit,
            "pain_point_match": self.pain_point_match,
        }

@dataclass
class ClassicalResult:
    rank: int
    capability_id: str
    capability_name: str
    domain: str
    topsis_score: float
    dimensions: DimensionBreakdown
    explanation: str
    impl_complexity: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "capability_id": self.capability_id,
            "capability_name": self.capability_name,
            "domain": self.domain,
            "topsis_score": round(self.topsis_score, 4),
            "dimensions": self.dimensions.as_dict(),
            "explanation": self.explanation,
            "impl_complexity": self.impl_complexity,
        }
        
@dataclass
class LLMRankedItem:
    rank: int
    capability_id: str
    capability_name: str
    domain: str = ""
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "capability_id": self.capability_id,
            "capability_name": self.capability_name,
            "domain": self.domain,
            "explanation": self.explanation,
        }

@dataclass
class LLMResult:
    ranked_items: list[LLMRankedItem]
    cot_reasoning: str = ""
    model_used: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ranked_items": [item.to_dict() for item in self.ranked_items],
            "cot_reasoning": self.cot_reasoning,
            "model_used": self.model_used,
        }

@dataclass
class HybridResult:
    classical: list[ClassicalResult]
    llm: LLMResult
    hybrid_ranking: list[str]
    classical_weight: float = 0.5
    llm_weight: float = 0.5
    company_id: str = ""

    def top_n(self, n: int = 5) -> list[str]:
        return self.hybrid_ranking[:n]

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_id": self.company_id,
            "hybrid_ranking": self.hybrid_ranking,
            "classical_weight": self.classical_weight,
            "llm_weight": self.llm_weight,
            "classical": [r.to_dict() for r in self.classical],
            "llm": self.llm.to_dict(),
        }
