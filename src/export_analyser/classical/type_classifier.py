from __future__ import annotations

from ..models import DataType

def classify(fields_present: set[str], roles: dict[str, str], n_rows: int) -> tuple[DataType, float]:
    role_vals = set(roles.values())
    has_date = "date" in fields_present or "created_at" in fields_present or "date" in role_vals
    has_amount = "amount" in fields_present or "numeric" in role_vals
    has_category = (
        "status" in fields_present or "channel" in fields_present
        or "product_name" in fields_present or "category" in role_vals
    )

    scores: dict[DataType, float] = {}

    ticket_signals = [
        "first_response_at" in fields_present,
        "ticket_id" in fields_present or "subject" in fields_present,
        "status" in fields_present,
        has_date,
    ]
    has_ticket_marker = ("first_response_at" in fields_present
                         or "ticket_id" in fields_present or "subject" in fields_present)
    if has_ticket_marker and "amount" not in fields_present:
        scores[DataType.support_tickets] = sum(ticket_signals) / len(ticket_signals)

    order_signals = [has_date, has_amount, has_category,
                     "order_id" in fields_present or "product_name" in fields_present]
    if has_date and has_amount:
        scores[DataType.orders] = sum(order_signals) / len(order_signals)

    lead_signals = ["lead_name" in fields_present, "stage" in fields_present,
                    "channel" in fields_present, has_date]
    if "lead_name" in fields_present or "stage" in fields_present:
        scores[DataType.crm_leads] = sum(lead_signals) / len(lead_signals)

    if "stock_quantity" in fields_present and "product_name" in fields_present:
        scores[DataType.inventory] = 1.0 if has_amount else 0.85

    if (n_rows <= 36 and has_date and has_amount
            and "order_id" not in fields_present and not has_ticket_marker):
        scores.setdefault(DataType.analytics, 0.6)

    if not scores:
        return DataType.unknown, 0.0
    best = max(scores, key=scores.get)
    return best, round(scores[best], 3)
