from __future__ import annotations

from dataclasses import dataclass

from src.catalog.pain_flags import PainFlags

from ..models import DataType, MetricSet
from .client import LLMUnavailable, call_json

_ALLOWED_FLAGS: dict[str, str] = {
    PainFlags.SLOW_RESPONSE: "slow customer-response times",
    PainFlags.HIGH_VOLUME_SUPPORT: "support team overwhelmed by message volume",
    PainFlags.REPETITIVE_SUPPORT: "answering the same questions repeatedly",
    PainFlags.MULTICHANNEL: "managing orders/conversations across multiple channels",
    PainFlags.STOCKOUTS_UNIVERSAL: "running out of stock / unpredictable demand",
    PainFlags.OVERSTOCK: "too much slow-moving stock",
    PainFlags.MANUAL_DATA_ENTRY: "manual data entry across systems",
    PainFlags.SLOW_ORDER_PROC: "slow order processing/fulfilment",
    PainFlags.MANUAL_RETURNS: "manual returns handling",
    PainFlags.LOW_REPEAT_PURCHASES: "low repeat purchase rate / churn",
}
_VALID = set(PainFlags.all_paths())

@dataclass
class SignalResult:
    enrichment: str
    pain_flags: dict[str, float]

def _metrics_lines(data_type: DataType, m: MetricSet) -> str:
    fields = []
    if m.total_records is not None:
        fields.append(f"records: {m.total_records}")
    if m.date_range_months:
        fields.append(f"date range: {m.date_range_months} months")
    if m.channels:
        fields.append(f"channels: {', '.join(m.channels)}")
    if m.avg_response_time_hours is not None:
        fields.append(f"avg first-response time: {m.avg_response_time_hours} hours")
    if m.open_items is not None and m.closed_items is not None:
        fields.append(f"open: {m.open_items}, resolved: {m.closed_items}")
    if m.avg_order_value is not None:
        fields.append(f"avg order value: {m.avg_order_value}")
    if m.seasonality_cv is not None:
        fields.append(f"seasonality (CV of monthly volume): {m.seasonality_cv}, peak {m.peak_month}")
    if m.fulfillment_null_pct is not None:
        fields.append(f"orders with no delivery date: {m.fulfillment_null_pct}%")
    return "\n".join(f"- {f}" for f in fields)

def _build_prompt(data_type: DataType, m: MetricSet) -> str:
    menu = "\n".join(f'  "{k}": {desc}' for k, desc in _ALLOWED_FLAGS.items())
    return (
        "You are a business analyst. Given these aggregated metrics from a "
        f"company's {data_type.value} export, identify operational pain points and "
        "write a concise 2-3 sentence summary for a recommendation system. "
        "Respond with JSON only.\n\n"
        f"Metrics:\n{_metrics_lines(data_type, m)}\n\n"
        "Score ONLY pain points from this menu that the metrics support (0.0-1.0); "
        f"use the exact keys:\n{menu}\n\n"
        'Return JSON: {"enrichment": "<2-3 sentences>", '
        '"pain_signals": {"<key>": <score>, ...}}'
    )

def extract_signals(data_type: DataType, m: MetricSet, *, model: str | None = None) -> SignalResult | None:
    try:
        parsed = call_json(_build_prompt(data_type, m), model=model)
    except LLMUnavailable:
        return None
    if not parsed:
        return None

    enrichment = str(parsed.get("enrichment") or "").strip()
    raw = parsed.get("pain_signals") or {}
    flags: dict[str, float] = {}
    for k, v in raw.items():
        if k in _VALID and k in _ALLOWED_FLAGS:
            try:
                score = float(v)
            except (TypeError, ValueError):
                continue
            if 0.0 <= score <= 1.0:
                flags[k] = round(score, 2)
    if not enrichment and not flags:
        return None
    return SignalResult(enrichment=enrichment, pain_flags=flags)
