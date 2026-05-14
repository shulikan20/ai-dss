from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_EU_COUNTRIES: frozenset[str] = frozenset({
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK"
})
_COUNTRY_TO_ISO2: dict[str, str] = {
    "austria": "AT",
    "belgium": "BE",
    "bulgaria": "BG",
    "cyprus": "CY",
    "czechia": "CZ",
    "czech republic": "CZ",
    "germany": "DE", 
    "denmark": "DK",
    "estonia": "EE",
    "spain": "ES",
    "finland": "FI",
    "france": "FR",
    "greece": "GR",
    "croatia": "HR",
    "hungary": "HU",
    "ireland": "IE",
    "italy": "IT",
    "lithuania": "LT",
    "luxembourg": "LU",
    "latvia": "LV",
    "malta": "MT",
    "netherlands": "NL",
    "poland": "PL",
    "portugal": "PT",
    "romania": "RO",
    "sweden": "SE",
    "slovenia": "SI",
    "slovakia": "SK",
    "ukraine": "UA",
    "united kingdom": "GB", "uk": "GB",
    "switzerland": "CH",
    "norway": "NO",
}
_TECH_LEVEL_MAP: dict[str, int] = {"low": 1, "medium": 2, "high": 3}


@dataclass
class CompanyProfile:
    company_id: str
    company_name: str = ""
    country: str = ""
    industry: str = ""
    bottleneck_description: str = ""
    active_domains: list[str] = field(default_factory=list)
    current_tools: list[str] = field(default_factory=list)
    order_count: int = 0
    history_months: int = 0
    export_types_available: list[str] = field(default_factory=list)
    has_structured_export: bool = False
    has_communication_logs: bool = False
    technical_level: int = 1
    implementation_support_requested: bool = False
    pain_point_flags: dict[str, bool] = field(default_factory=dict)
    open_notes: str = ""
    prior_ai_experience: str = ""
 
    @property
    def is_eu(self) -> bool:
        return self.country.upper() in _EU_COUNTRIES
 
    @property
    def confirmed_pain_points(self) -> set[str]:
        return {k for k, v in self.pain_point_flags.items() if v}

    @classmethod
    def from_json(cls, path: Path | str) -> CompanyProfile:
        source = Path(path)
        with source.open(encoding="utf-8") as f:
            raw: dict[str, Any] = json.load(f)
        raw.setdefault("_source_file", source.stem)
        return cls._parse(raw)
 
    @classmethod
    def _parse(cls, raw: dict[str, Any]) -> CompanyProfile:
        meta = raw.get("meta", {})
        universal = raw.get("universal", {})
        identity = universal.get("identity", {})
        tech_stack = universal.get("tech_stack", {})
        tech_cap = universal.get("technical_capability", {})
        data_av = universal.get("data_availability", {})
        ai_readiness = universal.get("ai_readiness", {})
        domain_context = raw.get("domain_context", {})
        processes_list: list[dict] = raw.get("processes") or []
        export_comp = raw.get("export_computed") or {}
        export_fields = export_comp.get("fields", {}) if isinstance(export_comp, dict) else {}
        unstructured = raw.get("unstructured_supplements") or []
        active_domains = [
            domain for domain, block in domain_context.items()
            if isinstance(block, dict) and block.get("active", False)
        ]

        parts = []
        for proc in processes_list:
            if not isinstance(proc, dict):
                continue
            bn = proc.get("bottleneck", {})
            desc = bn.get("description", "") if isinstance(bn, dict) else ""
            if desc:
                name = proc.get("name", "")
                parts.append(f"[{name}] {desc}" if name else desc)
        bottleneck = " | ".join(parts)

        order_count = int(export_fields.get("total_records") or 0)
        if not order_count:
            counts = [
                int(p.get("process_data", {}).get("record_count") or 0)
                for p in processes_list if isinstance(p, dict)
            ]
            order_count = max(counts, default=0)

        history_months = int(
            data_av.get("history_months")
            or export_fields.get("history_months")
            or 0
        )
        export_types = list(data_av.get("export_types_available") or [])
        current_tools = list(tech_stack.get("current_tools") or [])
        level_raw = str(tech_cap.get("level") or "low").lower()
        tech_level = _TECH_LEVEL_MAP.get(level_raw, 1)
        company_id = str(
            meta.get("company_id")
            or raw.get("company_id")
            or raw.get("_source_file", "unknown")
        )
        country_raw = str(identity.get("country") or "").strip()
        country = _COUNTRY_TO_ISO2.get(country_raw.lower(), country_raw.upper()[:2])
        pain_flags: dict[str, bool] = {}

        universal_procs = universal.get("processes", {})
        for key, val in universal_procs.items():
            if "pain" in key.lower() and isinstance(val, bool):
                pain_flags[f"universal.processes.{key}"] = val
 
        for domain, block in domain_context.items():
            if not isinstance(block, dict):
                continue
            for sub_key, sub_val in block.items():
                if isinstance(sub_val, dict):
                    for field_key, field_val in sub_val.items():
                        if "pain" in field_key.lower() and isinstance(field_val, bool):
                            pain_flags[f"{domain}.{sub_key}.{field_key}"] = field_val
                elif "pain" in sub_key.lower() and isinstance(sub_val, bool):
                    pain_flags[f"{domain}.{sub_key}"] = sub_val
 
        notes_parts = [
            item["content_summary"]
            for item in (unstructured if isinstance(unstructured, list) else [])
            if isinstance(item, dict) and item.get("content_summary")
        ]
        open_notes = " | ".join(notes_parts)
        attempts = ai_readiness.get("previous_ai_attempts") or []
        prior_ai = "; ".join(
            a.get("description", "") for a in attempts
            if isinstance(a, dict) and a.get("description")
        )
 
        return cls(
            company_id=company_id,
            company_name=str(identity.get("legal_name") or identity.get("company_name") or ""),
            country=country,
            industry=str(identity.get("industry_segment") or ""),
            bottleneck_description=bottleneck,
            active_domains=active_domains,
            current_tools=[t.lower().strip() for t in current_tools],
            order_count=order_count,
            history_months=history_months,
            export_types_available=export_types,
            has_structured_export=bool(
                export_types or data_av.get("has_structured_export")
            ),
            has_communication_logs=bool(data_av.get("has_communication_logs")),
            technical_level=max(1, min(3, tech_level)),
            implementation_support_requested=bool(
                universal.get("implementation_support_requested")
            ),
            pain_point_flags=pain_flags,
            open_notes=open_notes,
            prior_ai_experience=prior_ai,
        )
 
    def to_dict(self) -> dict[str, Any]:
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "country": self.country,
            "industry": self.industry,
            "bottleneck_description": self.bottleneck_description,
            "active_domains": self.active_domains,
            "current_tools": self.current_tools,
            "order_count": self.order_count,
            "history_months": self.history_months,
            "export_types_available": self.export_types_available,
            "has_structured_export": self.has_structured_export,
            "has_communication_logs": self.has_communication_logs,
            "technical_level": self.technical_level,
            "implementation_support_requested": self.implementation_support_requested,
            "pain_point_flags": self.pain_point_flags,
            "open_notes": self.open_notes,
            "prior_ai_experience": self.prior_ai_experience,
        }
 
    def __repr__(self) -> str:
        return (
            f"====== OUTPUT ======    "
            f"CompanyProfile(id={self.company_id!r}, "
            f"name={self.company_name!r}, "
            f"domains={self.active_domains}, "
            f"pain_points_confirmed={len(self.confirmed_pain_points)})"
            f"   ====== OUTPUT ======"
        )