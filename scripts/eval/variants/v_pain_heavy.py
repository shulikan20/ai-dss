from __future__ import annotations

from . import register
from ._weighted import WeightedClassicalVariant


@register
class VPainHeavy(WeightedClassicalVariant):
    name = "v_pain_heavy"
    description = (
        "Classical TOPSIS, pain-weighted "
        "(semantic 0.25 / pain 0.45 / data 0.20 / tech 0.10 / integ 0.00)."
    )
    weights = {
        "semantic_fit": 0.25,
        "integration_compat": 0.00,
        "data_readiness": 0.20,
        "tech_fit": 0.10,
        "pain_point_match": 0.45,
    }
