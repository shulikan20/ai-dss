"""
api/translator/questions — Question schema package.

Single source of truth for the questionnaire. Assembled from per-domain
modules for maintainability.

This package is read by two consumers:
  1. GET /api/questions (api/main.py) — serves it to React
  2. WebFormTranslator.translate() — maps answers to pain flags

To add a question:    add a dict to the relevant domain module
To add a domain:      create a new module + register in QUESTIONS below
To change wording:    update "text" or "help_text" in the domain module
To change pain flags: update the "pain_flags" list on the relevant options

No other files need changing.
"""

from __future__ import annotations

from api.translator.questions.types import (
    AnswerOption,
    ProfileFieldOption,
    Question,
    Domain,
)
from api.translator.questions.domains import DOMAINS
from api.translator.questions import (
    customer_support,
    ecommerce_ops,
    marketing,
    supply_chain,
    crm_sales,
    operations_backoffice,
)
from api.translator.questions.full_tier_extras import EXTRAS
from api.translator.questions.bottleneck_tags import TAGS


# ─────────────────────────────────────────────────────────────────────────
# Assembled question data — keyed by domain ID
# ─────────────────────────────────────────────────────────────────────────

_QUESTIONS: dict[str, list[Question]] = {
    "customer_support": customer_support.QUESTIONS,
    "ecommerce_ops": ecommerce_ops.QUESTIONS,
    "marketing": marketing.QUESTIONS,
    "supply_chain": supply_chain.QUESTIONS,
    "crm_sales": crm_sales.QUESTIONS,
    "operations_backoffice": operations_backoffice.QUESTIONS,
}


# ─────────────────────────────────────────────────────────────────────────
# Exported schema — this is what GET /api/questions returns
# ─────────────────────────────────────────────────────────────────────────

QUESTION_SCHEMA: dict = {
    "domains": DOMAINS,
    "questions": _QUESTIONS,
    "full_tier_extras": EXTRAS,
    "bottleneck_tags": TAGS,
}


# ─────────────────────────────────────────────────────────────────────────
# Helper functions — used by WebFormTranslator
# ─────────────────────────────────────────────────────────────────────────


def get_questions_for_tier(tier: str) -> dict[str, list[Question]]:
    """
    Returns only the domain questions that appear in the given tier.
    Full tier includes all questions.
    Standard tier excludes full-only questions.
    Quick tier returns an empty dict (no structured questions).
    """
    if tier == "quick":
        return {}

    result: dict[str, list[Question]] = {}
    for domain, questions in _QUESTIONS.items():
        filtered = [q for q in questions if tier in q["tier"]]
        if filtered:
            result[domain] = filtered
    return result


def get_all_catalog_pain_flags() -> set[str]:
    """
    Returns every unique pain flag path referenced anywhere in the schema.
    Used in Phase 1 catalog audit: compare against
    SELECT DISTINCT json_each.value FROM capabilities, json_each(mapped_pain_points)
    to verify all paths exist in catalog.db before the translator goes live.
    """
    flags: set[str] = set()
    for questions in _QUESTIONS.values():
        for question in questions:
            for option in question.get("options", []):
                flags.update(option.get("pain_flags", []))
    return flags


# Re-export types for backward compatibility
__all__ = [
    "QUESTION_SCHEMA",
    "get_questions_for_tier",
    "get_all_catalog_pain_flags",
    "AnswerOption",
    "ProfileFieldOption",
    "Question",
    "Domain",
]
