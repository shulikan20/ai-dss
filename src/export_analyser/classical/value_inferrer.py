from __future__ import annotations

import re
from collections import Counter

_SAMPLE = 200
_DATE_RE = re.compile(r"^\s*\d{4}[-/]\d{1,2}[-/]\d{1,2}([ T]\d{1,2}:\d{2})?")
_CURRENCY = re.compile(r"[€$£₴¥%\s ]|zł|usd|uah|pln|eur|gbp", re.IGNORECASE)

def _is_date(v: str) -> bool:
    return bool(_DATE_RE.match(v)) or bool(
        re.match(r"^\s*\d{1,2}[./]\d{1,2}[./]\d{2,4}", v)
    )

def _is_number(v: str) -> bool:
    s = _CURRENCY.sub("", v).strip()
    if not s or s in {"-", ".", ","}:
        return False
    if any(c.isalpha() for c in s):
        return False
    if s.count(",") and s.count("."):
        s = s.replace(".", "").replace(",", ".")
    elif s.count(","):
        s = s.replace(",", ".")
    try:
        float(s)
        return True
    except ValueError:
        return False

def infer_roles(records: list[dict], columns: list[str]) -> dict[str, str]:
    roles: dict[str, str] = {}
    for col in columns:
        vals = [r.get(col) for r in records[:_SAMPLE]]
        vals = [str(v).strip() for v in vals if v not in (None, "")]
        if not vals:
            roles[col] = "empty"
            continue
        n = len(vals)
        date_ratio = sum(_is_date(v) for v in vals) / n
        num_ratio = sum(_is_number(v) for v in vals) / n
        distinct = len(set(vals))
        uniq_ratio = distinct / n

        if date_ratio >= 0.6:
            roles[col] = "date"
        elif num_ratio >= 0.8:
            roles[col] = "numeric"
        elif distinct <= 12 and uniq_ratio <= 0.5:
            roles[col] = "category"
        else:
            roles[col] = "text"
    return roles


def role_counts(roles: dict[str, str]) -> Counter:
    return Counter(roles.values())
