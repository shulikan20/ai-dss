from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from src.ingestion.normalizers.base import BaseNormalizer

_DATE_COLS = [
    "order_date", "created_at", "Created at", "Date", "Order Date", "date_created", "OrderDate"
]
_STATUS_COLS = [
    "status", "Financial Status", "Order Status", "order_status", "fulfillment_status", "Status"
]
_CHANNEL_COLS = [
    "channel", "Source", "Sales Channel", "source", "sales_channel", "Channel", "origin", "platform"
]
_PRICE_COLS = [
    "Total", "total_price", "Order Total", "amount", "Amount", "grand_total", "revenue", "price", "subtotal"
]

_COMPLETED_STATUSES = {"Completed", "completed", "paid", "fulfilled", "delivered"}
_OUTCOME_STATUSES = _COMPLETED_STATUSES | {"Cancelled", "cancelled", "Returned", "returned", "refunded"}

_DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d.%m.%Y",
]

def _find_column(headers: list[str], candidates: list[str]) -> str | None:
    header_set = set(headers)
    for c in candidates:
        if c in header_set:
            return c
    return None

def _parse_date(value: str) -> datetime | None:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None

class OrderNormalizer(BaseNormalizer):
    @property
    def platform_name(self) -> str:
        return "order_normalizer"

    def normalize(self, raw: dict) -> dict[str, Any]:
        orders = raw.get("orders", [])
        if not orders:
            return {"total_records": 0}
        headers = list(orders[0].keys())
        total = len(orders)
        date_col = _find_column(headers, _DATE_COLS)
        status_col = _find_column(headers, _STATUS_COLS)
        channel_col = _find_column(headers, _CHANNEL_COLS)
        price_col, currency = self._detect_price_column(headers)
        dates: list[datetime] = []
        statuses: list[str] = []
        channels: list[str] = []
        prices: list[float] = []
        month_names: list[str] = []

        for order in orders:
            if not isinstance(order, dict):
                continue
            if date_col:
                dt = _parse_date(str(order.get(date_col) or ""))
                if dt:
                    dates.append(dt)
                    month_names.append(dt.strftime("%B"))
            if status_col:
                statuses.append(str(order.get(status_col) or ""))
            if channel_col:
                channels.append(str(order.get(channel_col) or ""))
            if price_col:
                try:
                    prices.append(float(order.get(price_col) or 0))
                except (ValueError, TypeError):
                    pass

        result: dict[str, Any] = {"total_records": total}

        if len(dates) >= 2:
            span_days = (max(dates) - min(dates)).days
            result["history_months"] = max(1, round(span_days / 30.44))

        if statuses:
            result["has_outcome_labels"] = any(s in _OUTCOME_STATUSES for s in statuses)
            completed = sum(1 for s in statuses if s in _COMPLETED_STATUSES)
            result["completed_order_rate"] = round(completed / total, 3)

        if channels:
            counts = Counter(ch for ch in channels if ch)
            result["channel_split"] = {
                ch.lower().replace(" ", "_"): round(n / total, 3)
                for ch, n in counts.items()
            }

        if month_names:
            month_counts = Counter(month_names)
            result["peak_months"] = [m for m, _ in month_counts.most_common(2)]

        if prices:
            result[f"avg_order_value_{currency}"] = round(sum(prices) / len(prices), 2)

        return result

    def _detect_price_column(self, headers: list[str]) -> tuple[str | None, str]:
        for col in headers:
            if col.startswith("price_") and len(col) > 6:
                return col, col.split("_", 1)[1]

        generic = _find_column(headers, _PRICE_COLS)
        return generic, "unknown"