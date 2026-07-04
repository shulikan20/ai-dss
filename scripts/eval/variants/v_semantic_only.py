from __future__ import annotations

from . import register
from ._weighted import WeightedClassicalVariant


@register
class VSemanticOnly(WeightedClassicalVariant):
    name = "v_semantic_only"
    description = "Classical TOPSIS, semantic-only ablation (semantic 1.00, all else 0.00)."
    weights = {
        "semantic_fit": 1.00,
        "integration_compat": 0.00,
        "data_readiness": 0.00,
        "tech_fit": 0.00,
        "pain_point_match": 0.00,
    }
