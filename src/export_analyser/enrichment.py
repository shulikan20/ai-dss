from __future__ import annotations

from src.catalog.pain_flags import PainFlags

from .models import DataType, MetricSet

def build_enrichment(data_type: DataType, m: MetricSet) -> str:
    bits: list[str] = []

    if m.total_records:
        span = f" over {m.date_range_months} months" if m.date_range_months else ""
        noun = {
            DataType.orders: "orders",
            DataType.support_tickets: "support tickets",
            DataType.crm_leads: "leads",
            DataType.inventory: "inventory items",
        }.get(data_type, "records")
        bits.append(f"Uploaded data shows {m.total_records} {noun}{span}.")

    if m.channels:
        if len(m.channels) > 1:
            bits.append(f"Sales/contact span {len(m.channels)} channels: {', '.join(m.channels[:4])}.")
        else:
            bits.append(f"Primary channel: {m.channels[0]}.")

    if m.avg_response_time_hours is not None:
        days = m.avg_response_time_hours / 24.0
        human = f"{days:.0f} days" if days >= 2 else f"{m.avg_response_time_hours:.0f} hours"
        bits.append(f"Average first-response time is about {human}.")

    if m.open_items is not None and m.closed_items is not None and (m.open_items + m.closed_items):
        total = m.open_items + m.closed_items
        rate = 100.0 * m.closed_items / total
        bits.append(f"{m.open_items} open vs {m.closed_items} resolved ({rate:.0f}% closed).")

    if m.avg_order_value is not None:
        bits.append(f"Average order value is {m.avg_order_value:.0f}.")

    if m.seasonality_cv is not None and m.seasonality_cv >= 0.4 and m.peak_month:
        bits.append(f"Demand is seasonal (peak {m.peak_month}).")

    if m.fulfillment_null_pct is not None and m.fulfillment_null_pct >= 30:
        bits.append(f"{m.fulfillment_null_pct:.0f}% of orders have no delivery date recorded.")

    return " ".join(bits)


_SUPPORT_FLAGS = frozenset({
    PainFlags.SLOW_RESPONSE,
    PainFlags.HIGH_VOLUME_SUPPORT,
    PainFlags.REPETITIVE_SUPPORT,
    PainFlags.TICKET_OVERLOAD,
})

def flag_grounded(flag: str, data_type: DataType, m: MetricSet) -> bool:
    if flag == PainFlags.SLOW_RESPONSE:
        return m.avg_response_time_hours is not None
    if flag in _SUPPORT_FLAGS:
        return data_type is DataType.support_tickets
    return True

def suggest_pain_flags(data_type: DataType, m: MetricSet) -> dict[str, float]:
    out: dict[str, float] = {}

    if m.avg_response_time_hours is not None:
        if m.avg_response_time_hours >= 48:
            out[PainFlags.SLOW_RESPONSE] = 0.95
        elif m.avg_response_time_hours >= 24:
            out[PainFlags.SLOW_RESPONSE] = 0.75

    if m.open_items is not None and m.closed_items is not None:
        total = m.open_items + m.closed_items
        if total >= 50 and m.open_items > 3 * max(1, m.closed_items):
            out[PainFlags.HIGH_VOLUME_SUPPORT] = 0.82

    if len(m.channels) >= 2:
        social = any(c.lower() in {"instagram", "facebook", "tiktok", "whatsapp"} for c in m.channels)
        out[PainFlags.MULTICHANNEL] = 0.9 if social else 0.7

    if m.seasonality_cv is not None and m.seasonality_cv >= 0.45:
        out[PainFlags.STOCKOUTS_UNIVERSAL] = 0.6

    return {f: c for f, c in out.items() if flag_grounded(f, data_type, m)}