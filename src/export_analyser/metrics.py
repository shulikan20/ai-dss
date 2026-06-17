from __future__ import annotations

import math
from collections import Counter

from .models import ColumnMap, DataType, MetricSet, ReadResult

_OPEN_STATUSES = {
    "new", "open", "pending", "processing", "in progress", "offen",
    "новий", "in bearbeitung", "nowe", "nouveau", " in bearbeitung",
}
_CLOSED_STATUSES = {
    "completed", "done", "solved", "closed", "fulfilled", "paid", "shipped",
    "abgeschlossen", "виконано", "zakonczone", "termine", "payé", "annulé",
    "refunded", "cancelled", "storniert",
}


def _series(records, col):
    return [r.get(col) for r in records] if col else []

def _to_float(v) -> float | None:
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    s = "".join(c for c in s if c.isdigit() or c in ".,-")
    if s.count(",") and s.count("."):
        s = s.replace(".", "").replace(",", ".")
    elif s.count(","):
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None

def extract_metrics(read: ReadResult, column_map: ColumnMap) -> MetricSet:
    import pandas as pd

    m = MetricSet(total_records=read.n_rows)
    records = read.records
    mp = column_map.mapping

    if "channel" in mp:
        ch = [str(v).strip() for v in _series(records, mp["channel"]) if v not in (None, "")]
        counts = Counter(ch)
        m.channels = [c for c, _ in counts.most_common()]
        if counts:
            m.channel_distribution = dict(counts.most_common(8))

    if "date" in mp or "created_at" in mp:
        date_col = mp.get("date") or mp.get("created_at")
        dt = pd.to_datetime(pd.Series(_series(records, date_col)), errors="coerce", format="mixed")
        dt = dt.dropna()
        if len(dt) >= 2:
            span_days = (dt.max() - dt.min()).days
            m.date_range_months = max(1, round(span_days / 30.0))
            by_month = dt.dt.to_period("M").value_counts().sort_index()
            if len(by_month):
                m.peak_month = str(by_month.idxmax())
                mean, std = by_month.mean(), by_month.std(ddof=0)
                m.seasonality_cv = round(float(std / mean), 3) if mean else None

    if "amount" in mp:
        vals = [x for x in (_to_float(v) for v in _series(records, mp["amount"])) if x is not None]
        if vals:
            m.avg_order_value = round(sum(vals) / len(vals), 2)

    if "delivery_date" in mp:
        col = _series(records, mp["delivery_date"])
        if col:
            nulls = sum(1 for v in col if v in (None, "", "null"))
            m.fulfillment_null_pct = round(100.0 * nulls / len(col), 1)

    if "status" in mp:
        sv = [str(v).strip().lower() for v in _series(records, mp["status"]) if v not in (None, "")]
        if sv:
            m.open_items = sum(1 for s in sv if s in _OPEN_STATUSES)
            m.closed_items = sum(1 for s in sv if s in _CLOSED_STATUSES)
            m.status_distribution = dict(Counter(sv).most_common(8))

    created_col = mp.get("created_at") or mp.get("date")
    if (column_map.data_type is DataType.support_tickets
            and created_col and "first_response_at" in mp):
        created = pd.to_datetime(pd.Series(_series(records, created_col)), errors="coerce", format="mixed")
        first = pd.to_datetime(pd.Series(_series(records, mp["first_response_at"])), errors="coerce", format="mixed")
        delta = (first - created).dropna()
        if len(delta):
            hours = delta.dt.total_seconds() / 3600.0
            hours = hours[hours >= 0]
            if len(hours):
                m.avg_response_time_hours = round(float(hours.mean()), 1)

    return m
