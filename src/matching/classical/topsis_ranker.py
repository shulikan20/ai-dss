from __future__ import annotations

import numpy as np

from config import CFG
from src.models.catalog_item import Capability, ImplComplexity, RankedCandidate
from src.models.company_profile import CompanyProfile

_DIMENSIONS = [
    "semantic_fit",
    "integration_compat",
    "data_readiness",
    "tech_fit",
    "pain_point_match",
]

# CFG.TOPSIS_FIXED_REFERENCE 
_DIM_BOUNDS: dict[str, tuple[float, float]] = {}

def _apply_fixed_bounds(matrix: np.ndarray) -> np.ndarray:
    out = matrix.copy()
    for j, dim in enumerate(_DIMENSIONS):
        lo, hi = _DIM_BOUNDS.get(dim, (0.0, 1.0))
        if hi > lo:
            out[:, j] = np.clip((out[:, j] - lo) / (hi - lo), 0.0, 1.0)
    return out

def _base_name(slug: str) -> str:
    return slug.lower().split("_")[0]

def _compute_integration_compat(cap: Capability, profile: CompanyProfile) -> float:
    if not cap.available_integrations:
        return 0.5

    profile_bases = {_base_name(t) for t in profile.current_tools}
    cap_bases = {_base_name(i) for i in cap.available_integrations}

    if not cap_bases:
        return 0.5

    overlap = profile_bases & cap_bases
    return len(overlap) / len(cap_bases)

def _compute_data_readiness(cap: Capability, profile: CompanyProfile) -> float:
    score = 1.0

    if not cap.works_without_data and profile.order_count == 0 and not profile.has_structured_export:
        score *= 0.3

    if cap.required_data_types:
        satisfied = sum(
            1 for t in cap.required_data_types
            if t in (profile.export_types_available or [])
        )
        type_ratio = satisfied / len(cap.required_data_types)
        score *= type_ratio

    gate = cap.min_history_months_gate or 0
    if gate > 0:
        if profile.history_months >= gate:
            pass
        elif profile.history_months == 0:
            score *= 0.4
        else:
            ratio = min(1.0, profile.history_months / gate)
            score *= max(0.4, ratio)

    return float(np.clip(score, 0.0, 1.0))

def _compute_tech_fit(cap: Capability, profile: CompanyProfile) -> float:
    gap = profile.technical_level - cap.min_technical_capability
    if gap >= 0:
        return 1.0
    elif gap == -1:
        return 0.5
    else:
        return 0.2

def _compute_pain_point_match(cap: Capability, profile: CompanyProfile) -> float:
    if not cap.mapped_pain_points:
        return 0.5

    company_points = profile.confirmed_pain_points  # set[str] @property
    if not company_points:
        return 0.5

    cap_points = set(cap.mapped_pain_points)
    overlap = cap_points & company_points
    return len(overlap) / len(cap_points)

def _topsis_fixed_reference(matrix: np.ndarray, weights: np.ndarray) -> np.ndarray:
    scaled = _apply_fixed_bounds(matrix)
    weighted = scaled * weights
    ideal = weights
    dist_ideal = np.sqrt(((weighted - ideal) ** 2).sum(axis=1))
    dist_anti = np.sqrt((weighted ** 2).sum(axis=1))
    denom = dist_ideal + dist_anti
    return np.where(denom == 0.0, 0.0, dist_anti / np.where(denom == 0.0, 1.0, denom))

def _topsis_relative(matrix: np.ndarray, weights: np.ndarray) -> np.ndarray:
    if matrix.shape[0] == 1:
        return np.array([1.0])

    col_norms = np.linalg.norm(matrix, axis=0)
    col_norms[col_norms == 0] = 1.0
    normed = matrix / col_norms
    weighted = normed * weights
    ideal = weighted.max(axis=0)
    anti_ideal = weighted.min(axis=0)
    dist_ideal = np.sqrt(((weighted - ideal) ** 2).sum(axis=1))
    dist_anti = np.sqrt(((weighted - anti_ideal) ** 2).sum(axis=1))
    denom = dist_ideal + dist_anti
    denom[denom == 0] = 1e-10
    return dist_anti / denom

def _topsis(matrix: np.ndarray, weights: np.ndarray) -> np.ndarray:
    if matrix.shape[0] == 0:
        return np.array([])
    if CFG.TOPSIS_FIXED_REFERENCE:
        return _topsis_fixed_reference(matrix, weights)
    return _topsis_relative(matrix, weights)

class TOPSISRanker:
    def rank(
        self,
        candidates: list[tuple[Capability, float]],
        profile: CompanyProfile,
        cf_scores: dict[str, float] | None = None,
        impl_complexity_map: dict[str, ImplComplexity] | None = None,
    ) -> list[RankedCandidate]:
        if not candidates:
            return []

        impl_map = impl_complexity_map or {}
        dim_rows: list[dict[str, float]] = []
        for cap, ce_score in candidates:
            dim_rows.append({
                "semantic_fit": ce_score,
                "integration_compat": _compute_integration_compat(cap, profile),
                "data_readiness": _compute_data_readiness(cap, profile),
                "tech_fit": _compute_tech_fit(cap, profile),
                "pain_point_match": _compute_pain_point_match(cap, profile),
            })

        weights = np.array(
            [CFG.TOPSIS_WEIGHTS[d] for d in _DIMENSIONS],
            dtype=np.float64,
        )
        matrix = np.array(
            [[row[d] for d in _DIMENSIONS] for row in dim_rows],
            dtype=np.float64,
        )

        closeness = _topsis(matrix, weights)

        ranked_candidates = [
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

        return sorted(ranked_candidates, key=lambda r: -r.topsis_score)