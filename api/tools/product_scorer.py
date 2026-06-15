from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_W_PLATFORM = 0.35
_W_COMPLEXITY = 0.25
_W_SIZE = 0.20
_W_PRICE = 0.20
_NEUTRAL = 0.5 
_TEAM_SIZE_BUCKET = {
    "1-5": "micro",
    "6-25": "small",
    "26-100": "medium",
    "100+": "medium",
}
_COMPLEXITY_REQUIREMENT = {"no_code": 1, "low_code": 2, "developer": 3}
_PRICE_ORDER = {"free": 0, "starter": 1, "growth": 2, "enterprise": 3}
_AFFORDABLE_MAX = {"micro": 1, "small": 2, "medium": 3}
_SIZE_ORDER = {"micro": 0, "small": 1, "medium": 2}


@dataclass(frozen=True)
class ScoredProduct:
    product: Any
    fit_score: float
    best_fit: bool


def _platform_score(product: Any, profile: Any) -> float:
    integrations = getattr(product, "platform_integrations", None)
    if not integrations:
        return _NEUTRAL
    tools = {str(t).lower() for t in getattr(profile, "current_tools", []) or []}
    if not tools:
        return _NEUTRAL
    available = {str(i).lower() for i in integrations}
    return 1.0 if tools & available else 0.2


def _complexity_score(product: Any, profile: Any) -> float:
    required = _COMPLEXITY_REQUIREMENT.get(
        getattr(product, "setup_complexity", None) or ""
    )
    if required is None:
        return _NEUTRAL
    tech = int(getattr(profile, "technical_level", 1) or 1)
    if tech >= required:
        return 1.0
    if required - tech == 1:
        return 0.5
    return 0.2


def _size_score(product: Any, bucket: str | None) -> float:
    fit = getattr(product, "company_size_fit", None)
    if bucket is None:
        return _NEUTRAL
    if not fit or fit == "any":
        return 0.75
    if fit == bucket:
        return 1.0
    gap = abs(_SIZE_ORDER.get(fit, 1) - _SIZE_ORDER.get(bucket, 1))
    return 0.5 if gap == 1 else 0.25


def _price_score(product: Any, bucket: str | None) -> float:
    tier = _PRICE_ORDER.get(getattr(product, "price_tier", None) or "")
    if tier is None or bucket is None:
        return _NEUTRAL
    affordable_max = _AFFORDABLE_MAX.get(bucket, 3)
    if tier <= affordable_max:
        return 1.0
    if tier - affordable_max == 1:
        return 0.5
    return 0.2


def score_products_for_profile(
    products: list[Any],
    profile: Any,
    team_size: str | None = None,
) -> list[ScoredProduct]:
    if not products:
        return []

    bucket = _TEAM_SIZE_BUCKET.get(team_size or "")

    scored: list[ScoredProduct] = []
    for p in products:
        composite = (
            _W_PLATFORM * _platform_score(p, profile)
            + _W_COMPLEXITY * _complexity_score(p, profile)
            + _W_SIZE * _size_score(p, bucket)
            + _W_PRICE * _price_score(p, bucket)
        )
        scored.append(ScoredProduct(product=p, fit_score=round(composite, 4), best_fit=False))

    scored.sort(key=lambda s: s.fit_score, reverse=True)
    return [
        ScoredProduct(product=s.product, fit_score=s.fit_score, best_fit=(i == 0))
        for i, s in enumerate(scored)
    ]
