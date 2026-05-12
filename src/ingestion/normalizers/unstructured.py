from __future__ import annotations

import csv
import json
import io
from typing import Any

class UnstructuredHandler:
    MAX_CHARS = 4000  # avoiding bloating the LLM prompt

    def extract_text(self, raw: dict) -> str:
        if raw.get("raw_text"):
            return self._truncate(str(raw["raw_text"]))

        orders = raw.get("orders", [])
        source = raw.get("source_file", "")

        if not orders:
            return ""

        ext = source.rsplit(".", 1)[-1].lower() if "." in source else ""

        try:
            if ext in ("csv", "") and isinstance(orders, list) and orders:
                return self._truncate(self._from_records(orders))
            elif ext == "json" or isinstance(orders, (dict, list)):
                return self._truncate(self._from_json(orders))
            else:
                return ""
        except Exception:
            return ""

    def _from_records(self, records: list[dict]) -> str:
        if not records:
            return ""
        lines = []
        headers = list(records[0].keys())
        lines.append(" | ".join(headers))
        for row in records[:50]:
            lines.append(" | ".join(str(row.get(h, "")) for h in headers))
        if len(records) > 50:
            lines.append(f"... ({len(records) - 50} more rows)")
        return "\n".join(lines)

    def _from_json(self, data: Any) -> str:
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _truncate(self, text: str) -> str:
        if len(text) <= self.MAX_CHARS:
            return text
        return text[:self.MAX_CHARS] + f"\n... [truncated at {self.MAX_CHARS} chars]"