from __future__ import annotations

from . import register
from ._weighted import WeightedClassicalVariant


@register
class VBalanced(WeightedClassicalVariant):
    name = "v_balanced"
    description = (
        "Classical TOPSIS, balanced "
        "(semantic 0.40 / pain 0.40 / data 0.10 / tech 0.10 / integ 0.00)."
    )
    weights = {
        "semantic_fit": 0.40,
        "integration_compat": 0.00,
        "data_readiness": 0.10,
        "tech_fit": 0.10,
        "pain_point_match": 0.40,
    }
