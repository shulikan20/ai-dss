from __future__ import annotations

from ..models import ColumnMap, DataType, ReadResult
from .client import LLMUnavailable, call_json

_STANDARD_FIELDS = [
    "order_id", "date", "status", "amount", "channel", "product_name", "quantity",
    "customer", "city", "country", "delivery_date", "delivery_service", "manager",
    "email", "phone", "ticket_id", "subject", "created_at", "first_response_at",
    "lead_name", "stage", "stock_quantity",
]
_SYSTEM = (
    "You are a business-data analyst. You map export-file columns to standard "
    "field names. The headers may be in any language (English, German, Ukrainian, "
    "Polish, French, …). Respond with JSON only, no prose."
)

def _build_prompt(columns: list[str], sample_rows: list[dict]) -> str:
    rows_txt = []
    for i, row in enumerate(sample_rows[:3], 1):
        vals = {c: row.get(c) for c in columns}
        rows_txt.append(f"Sample row {i}: {vals}")
    return (
        f"{_SYSTEM}\n\n"
        f"Headers: {columns}\n"
        + "\n".join(rows_txt)
        + "\n\nStandard field names you may use: " + ", ".join(_STANDARD_FIELDS)
        + "\nValid data_type values: orders, support_tickets, crm_leads, inventory, analytics, unknown."
        + '\n\nReturn JSON exactly like: '
        '{"platform": "...", "data_type": "...", "column_map": {"date": "<header>", "amount": "<header>"}}'
        "\nOnly include fields you are confident about. Use the file's exact header strings as values."
    )

def map_columns(read: ReadResult, *, model: str | None = None) -> ColumnMap | None:
    if not read.columns:
        return None
    try:
        parsed = call_json(_build_prompt(read.columns, read.records), model=model)
    except LLMUnavailable:
        return None
    if not parsed:
        return None

    raw_map = parsed.get("column_map") or {}
    valid_cols = set(read.columns)
    mapping = {
        std: src for std, src in raw_map.items()
        if std in _STANDARD_FIELDS and isinstance(src, str) and src in valid_cols
    }
    try:
        data_type = DataType(str(parsed.get("data_type", "unknown")))
    except ValueError:
        data_type = DataType.unknown
        
    confidence = round(min(1.0, len(mapping) / 4.0), 3) if mapping else 0.0
    return ColumnMap(
        platform=str(parsed.get("platform") or "") or None,
        data_type=data_type,
        mapping=mapping,
        confidence=confidence,
        method="LA1-llm",
    )
