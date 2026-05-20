from __future__ import annotations

from src.models.company_profile import CompanyProfile
from src.models.recommendation import ClassicalResult, HybridResult, LLMResult

class HybridAggregator:
    _DATA_RICH_CLASSICAL_WEIGHT: float = 0.60
    _DATA_RICH_LLM_WEIGHT: float = 0.40
    _DEFAULT_CLASSICAL_WEIGHT: float = 0.40
    _DEFAULT_LLM_WEIGHT: float = 0.60
    _MIN_CONFIRMED_PAIN_POINTS: int = 2

    def aggregate(
        self,
        profile: CompanyProfile,
        classical: list[ClassicalResult],
        llm: LLMResult,
    ) -> HybridResult:
        classical_weight, llm_weight = self._determine_weights(profile)
        c_scores: dict[str, float] = {
            r.capability_id: r.topsis_score for r in classical
        }
        l_scores: dict[str, float] = self._llm_rank_to_scores(llm)
        all_ids = set(c_scores) | set(l_scores)
        hybrid_scores: dict[str, float] = {
            cap_id: (
                classical_weight * c_scores.get(cap_id, 0.0)
                + llm_weight * l_scores.get(cap_id, 0.0)
            )
            for cap_id in all_ids
        }
        hybrid_ranking = sorted(
            hybrid_scores, key=lambda cid: hybrid_scores[cid], reverse=True
        )

        return HybridResult(
            classical=classical,
            llm=llm,
            hybrid_ranking=hybrid_ranking,
            classical_weight=classical_weight,
            llm_weight=llm_weight,
            company_id=profile.company_id,
        )
    
    def _determine_weights(
        self, profile: CompanyProfile
    ) -> tuple[float, float]:
        confirmed_pain_points = sum(
            1 for v in profile.pain_point_flags.values() if v
        )
        has_export = bool(profile.export_types_available)

        if confirmed_pain_points >= self._MIN_CONFIRMED_PAIN_POINTS and has_export:
            return self._DATA_RICH_CLASSICAL_WEIGHT, self._DATA_RICH_LLM_WEIGHT
        return self._DEFAULT_CLASSICAL_WEIGHT, self._DEFAULT_LLM_WEIGHT

    @staticmethod
    def _llm_rank_to_scores(llm: LLMResult) -> dict[str, float]:
        return {item.capability_id: 1.0 / item.rank for item in llm.ranked_items}