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
    TOPSISRanker,
)
from src.models.catalog_item import RankedCandidate
from config import CFG
from . import VariantContext, VariantEngine, register

_NEUTRAL_DATA_READINESS = 0.5

def _data_not_collected(profile) -> bool:
    return (
        profile.order_count == 0
        and not profile.has_structured_export
        and not profile.export_types_available
        and profile.history_months == 0
    )

class NeutralDataRanker(TOPSISRanker):
    def rank(self, candidates, profile, cf_scores=None, impl_complexity_map=None):
        if not candidates:
            return []

        impl_map = impl_complexity_map or {}
        use_neutral = _data_not_collected(profile)

        dim_rows: list[dict[str, float]] = []
        for cap, ce_score in candidates:
            dr = _NEUTRAL_DATA_READINESS if use_neutral else _compute_data_readiness(cap, profile)
            dim_rows.append(
                {
                    "semantic_fit": ce_score,
                    "integration_compat": _compute_integration_compat(cap, profile),
                    "data_readiness": dr,
                    "tech_fit": _compute_tech_fit(cap, profile),
                    "pain_point_match": _compute_pain_point_match(cap, profile),
                }
            )

        weights_dict = dict(CFG.TOPSIS_WEIGHTS)
        weights = np.array([weights_dict[d] for d in _DIMENSIONS], dtype=np.float64)
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


@register
class V4NeutralData(VariantEngine):
    name = "v4_neutral_data"
    description = "Classical + neutral 0.5 data_readiness when data fields not collected"
    pipeline_label = "classical_fallback"

    def __init__(self, ctx: VariantContext) -> None:
        super().__init__(ctx)
        base = ctx.get_classical()
        self._engine = ClassicalEngine(
            repo=base._repo,
            embedder=base._embedder,
            retriever=base._retriever,
            reranker=base._reranker,
            ranker=NeutralDataRanker(),
            explainer=base._explainer,
            top_k=base._top_k,
        )

    def match(self, profile):
        return self._engine.match(profile)
