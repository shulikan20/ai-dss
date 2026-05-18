from __future__ import annotations

import dataclasses

from src.models.catalog_item import Capability, ImplComplexity, RankedCandidate
from src.models.company_profile import CompanyProfile
from src.models.recommendation import ClassicalResult, DimensionBreakdown
from src.matching.classical.topsis_ranker import _base_name

_PAIN_LABELS: dict[str, str] = {
    "universal.processes.pain_repetitive_support": "repetitive support tasks",
    "universal.processes.pain_slow_response": "slow response times",
    "universal.processes.pain_ticket_overload": "ticket overload",
    "universal.processes.pain_manual_content_creation": "manual content creation",
    "universal.processes.pain_low_marketing_roi": "low marketing ROI",
    "universal.processes.pain_manual_data_entry": "manual data entry",
    "universal.processes.pain_manual_invoicing": "manual invoicing",
    "universal.processes.pain_no_data_insights": "lack of data insights",
    "universal.processes.pain_stockouts": "stockout problems",
    "universal.processes.pain_overstock": "overstock issues",
    "universal.processes.pain_supplier_tracking": "supplier tracking gaps",
    "ecommerce_ops.pain_points.pain_manual_returns": "manual returns handling",
    "ecommerce_ops.pain_points.pain_inventory_tracking": "inventory tracking issues",
    "crm_sales.pipeline.pain_slow_followup": "slow sales follow-up",
    "crm_sales.pipeline.pain_unclear_reporting": "unclear pipeline reporting",
}

def _pain_label(key: str) -> str:
    if key in _PAIN_LABELS:
        return _PAIN_LABELS[key]
    
    last = key.split(".")[-1]
    if last.startswith("pain_"):
        last = last[5:]
    return last.replace("_", " ")


def _matched_tools(cap: Capability, profile: CompanyProfile) -> list[str]:
    cap_bases = {_base_name(i): i for i in cap.available_integrations}
    matched = []
    for tool in profile.current_tools:
        base = _base_name(tool)
        if base in cap_bases:
            matched.append(tool)
    return matched

def _build_explanation(
    candidate: RankedCandidate,
    profile: CompanyProfile,
) -> str:
    cap = candidate.capability
    frags: list[str] = []
    matched_pain = sorted(
        set(cap.mapped_pain_points) & profile.confirmed_pain_points,
        key=lambda k: _pain_label(k),
    )

    if matched_pain and candidate.pain_point_match >= 0.5:
        labels = ", ".join(_pain_label(k) for k in matched_pain[:3])
        frags.append(f"Directly addresses your confirmed pain points: {labels}.")
    elif candidate.semantic_fit >= 0.70:
        frags.append("Strong semantic alignment with your described bottleneck.")
    elif candidate.semantic_fit >= 0.50:
        frags.append("Matches several aspects of your described challenges.")
    else:
        frags.append("Relevant to your business domain.")

    tools = _matched_tools(cap, profile)
    if tools:
        tool_str = ", ".join(t.capitalize() for t in tools[:3])
        if candidate.integration_compat >= 0.60:
            frags.append(f"Integrates natively with your existing {tool_str}.")
        else:
            frags.append(f"Compatible with {tool_str} from your current stack.")

    if candidate.data_readiness < 0.60:
        cap_obj = cap
        if not cap_obj.works_without_data and profile.order_count == 0:
            frags.append(
                "Works best once you have historical order data connected — "
                "results will improve significantly with a data export."
            )
        elif cap_obj.min_history_months_gate and profile.history_months < cap_obj.min_history_months_gate:
            needed = cap_obj.min_history_months_gate
            have = profile.history_months
            frags.append(
                f"Optimal performance requires {needed}+ months of data; "
                f"you currently have {have} months."
            )
        elif cap_obj.required_data_types:
            missing = [t for t in cap_obj.required_data_types
                       if t not in (profile.export_types_available or [])]
            if missing:
                frags.append(
                    f"Full functionality requires {', '.join(missing)} data — "
                    "consider uploading this export for better results."
                )

    impl = candidate.impl_complexity
    if impl == ImplComplexity.MEDIUM:
        frags.append(
            "Requires some technical setup — "
            "implementation support is recommended."
        )
    elif impl == ImplComplexity.HIGH:
        frags.append(
            "Significant technical implementation — "
            "professional setup is strongly recommended."
        )

    return " ".join(frags)

class ExplanationGenerator:
    def generate(
        self,
        candidate: RankedCandidate,
        profile: CompanyProfile,
        rank: int,
        impl_complexity_map: dict[str, ImplComplexity] | None = None,
    ) -> ClassicalResult:
        impl = candidate.impl_complexity
        if impl is None and impl_complexity_map:
            impl = impl_complexity_map.get(candidate.capability.capability_id)

        explanation = _build_explanation(candidate, profile)

        dimensions = DimensionBreakdown(
            semantic_fit=round(candidate.semantic_fit, 4),
            integration_compat=round(candidate.integration_compat, 4),
            data_readiness=round(candidate.data_readiness, 4),
            tech_fit=round(candidate.tech_fit, 4),
            pain_point_match=round(candidate.pain_point_match, 4),
        )

        return ClassicalResult(
            rank=rank,
            capability_id=candidate.capability.capability_id,
            capability_name=candidate.capability.name,
            domain=candidate.capability.domain,
            topsis_score=round(candidate.topsis_score, 4),
            dimensions=dimensions,
            explanation=explanation,
            impl_complexity=impl.value if impl is not None else None,
        )