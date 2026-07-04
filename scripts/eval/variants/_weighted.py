from __future__ import annotations

from typing import ClassVar

import numpy as np

from src.matching.classical.classical_engine import ClassicalEngine
from src.matching.classical.topsis_ranker import (
    _DIMENSIONS,
    _compute_data_readiness,
    _compute_integration_compat,
    _compute_pain_point_match,
    _compute_tech_fit,
    _topsis,
)
from src.matching.classical.topsis_ranker import TOPSISRanker
from src.models.catalog_item import RankedCandidate
from . import VariantContext, VariantEngine


class WeightedTOPSISRanker(TOPSISRanker):
    def __init__(self, weights: dict[str, float]) -> None:
        missing = [d for d in _DIMENSIONS if d not in weights]
        if missing:
            raise ValueError(
                f"WeightedTOPSISRanker is missing weights for {missing}; "
                f"all of {_DIMENSIONS} must be provided."
            )
        extra = [k for k in weights if k not in _DIMENSIONS]
        if extra:
            raise ValueError(f"WeightedTOPSISRanker got unknown dimension(s) {extra}")
        if sum(weights.values()) <= 0:
            raise ValueError("WeightedTOPSISRanker weights must sum to a positive value")
        self._weights = {d: float(weights[d]) for d in _DIMENSIONS}

    def rank(
        self,
        candidates,
        profile,
        cf_scores=None,
        impl_complexity_map=None,
    ) -> list[RankedCandidate]:
        if not candidates:
            return []

        impl_map = impl_complexity_map or {}

        dim_rows: list[dict[str, float]] = []
        for cap, ce_score in candidates:
            dim_rows.append(
                {
                    "semantic_fit": ce_score,
                    "integration_compat": _compute_integration_compat(cap, profile),
                    "data_readiness": _compute_data_readiness(cap, profile),
                    "tech_fit": _compute_tech_fit(cap, profile),
                    "pain_point_match": _compute_pain_point_match(cap, profile),
                }
            )

        weights = np.array([self._weights[d] for d in _DIMENSIONS], dtype=np.float64)
        matrix = np.array(
            [[row[d] for d in _DIMENSIONS] for row in dim_rows],
            dtype=np.float64,
        )

        closeness = _topsis(matrix, weights)

        ranked = [
            RankedCandidate(
                capability=cap,
                topsis_score=float(closeness[i]),
                semantic_fit=dim_rows[i]["semantic_fit"],
                integration_compat=dim_rows[i]["integration_compat"],
                data_readiness=dim_rows[i]["data_readiness"],
                tech_fit=dim_rows[i]["tech_fit"],
                pain_point_match=dim_rows[i]["pain_point_match"],
                impl_complexity=impl_map.get(cap.capability_id),
            )
            for i, (cap, _) in enumerate(candidates)
        ]
        return sorted(ranked, key=lambda r: -r.topsis_score)


class WeightedClassicalVariant(VariantEngine):
    pipeline_label = "classical_fallback"
    weights: ClassVar[dict[str, float]]

    def __init__(self, ctx: VariantContext) -> None:
        super().__init__(ctx)
        base = ctx.get_classical()
        self._engine = ClassicalEngine(
            repo=base._repo,
            embedder=base._embedder,
            retriever=base._retriever,
            reranker=base._reranker,
            ranker=WeightedTOPSISRanker(self.weights),
            explainer=base._explainer,
            top_k=base._top_k,
        )

    def match(self, profile):
        return self._engine.match(profile)
