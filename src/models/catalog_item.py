from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class ImplComplexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class Capability:
    capability_id: str
    name: str
    domain: str
    use_case_category: str = ""
    task_type_target: str = ""
    description: str = ""
    bottleneck_keywords: list[str] = field(default_factory=list)
    works_without_data: bool = True
    required_data_types: list[str] = field(default_factory=list)
    min_history_months_gate: int = 0
    min_technical_capability: int = 1
    available_integrations: list[str] = field(default_factory=list)
    mapped_pain_points: list[str] = field(default_factory=list)
    primary_outcome: str = ""
    secondary_outcomes: list[str] = field(default_factory=list)
    time_to_value_weeks_min: int | None = None
    time_to_value_weeks_max: int | None = None

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> Capability:
        def _parse_json_list(val: Any) -> list[str]:
            if not val:
                return []
            if isinstance(val, list):
                return [str(x) for x in val]
            try:
                parsed = json.loads(val)
                return [str(x) for x in parsed] if isinstance(parsed, list) else []
            except (json.JSONDecodeError, TypeError):
                return []

        return cls(
            capability_id=str(row["capability_id"]),
            name=str(row["name"]),
            domain=str(row["domain"]),
            use_case_category=str(row.get("use_case_category") or ""),
            task_type_target=str(row.get("task_type_target") or ""),
            description=str(row.get("description") or ""),
            bottleneck_keywords=_parse_json_list(row.get("bottleneck_keywords")),
            works_without_data=bool(int(row.get("works_without_data") or 1)),
            required_data_types=_parse_json_list(row.get("required_data_types")),
            min_history_months_gate=int(row.get("min_history_months_gate") or 0),
            min_technical_capability=int(row.get("min_technical_capability") or 1),
            available_integrations=[],
            mapped_pain_points=_parse_json_list(row.get("mapped_pain_points")),
            primary_outcome=str(row.get("primary_outcome") or ""),
            secondary_outcomes=_parse_json_list(row.get("secondary_outcomes")),
            time_to_value_weeks_min=(
                int(row["time_to_value_weeks_min"])
                if row.get("time_to_value_weeks_min") is not None else None
            ),
            time_to_value_weeks_max=(
                int(row["time_to_value_weeks_max"])
                if row.get("time_to_value_weeks_max") is not None else None
            ),
        )

    def __repr__(self) -> str:
        return f"Capability(id={self.capability_id!r}, domain={self.domain!r}, name={self.name!r})"

@dataclass
class Product:
    product_id: str
    capability_id: str
    name: str
    vendor: str = ""
    url: str = ""
    integrations: list[str] = field(default_factory=list)
    gdpr_compliant: bool = False
    deployment_model: str  = "saas"
    pricing_model: str  = "freemium"
    has_free_tier: bool = False
    cost_tier: str  = "low"
    cost_notes: str  = ""
    implementation_effort: str  = "low"
    min_technical_capability: int = 1
    min_history_months: int | None = None
    min_record_count: int | None = None
    works_with_limited_data: bool = True
    data_requirement_notes: str = ""
    setup_notes: str = ""
    notes: str = ""

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> Product:
        def _parse_json_list(val: Any) -> list[str]:
            if not val:
                return []
            if isinstance(val, list):
                return [str(x) for x in val]
            try:
                parsed = json.loads(val)
                return [str(x) for x in parsed] if isinstance(parsed, list) else []
            except (json.JSONDecodeError, TypeError):
                return []

        return cls(
            product_id=str(row["product_id"]),
            capability_id=str(row["capability_id"]),
            name=str(row["name"]),
            vendor=str(row.get("vendor") or ""),
            url=str(row.get("url") or ""),
            integrations=_parse_json_list(row.get("integrations")),
            gdpr_compliant=bool(int(row.get("gdpr_compliant") or 0)),
            deployment_model=str(row.get("deployment_model") or "saas"),
            pricing_model=str(row.get("pricing_model") or "freemium"),
            has_free_tier=bool(int(row.get("has_free_tier") or 0)),
            cost_tier=str(row.get("cost_tier") or "low"),
            cost_notes=str(row.get("cost_notes") or ""),
            implementation_effort=str(row.get("implementation_effort") or "low"),
            min_technical_capability=int(row.get("min_technical_capability") or 1),
            min_history_months=(
                int(row["min_history_months"])
                if row.get("min_history_months") is not None else None
            ),
            min_record_count=(
                int(row["min_record_count"])
                if row.get("min_record_count") is not None else None
            ),
            works_with_limited_data=bool(int(row.get("works_with_limited_data") or 1)),
            data_requirement_notes=str(row.get("data_requirement_notes") or ""),
            setup_notes=str(row.get("setup_notes") or ""),
            notes=str(row.get("notes") or ""),
        )

    def __repr__(self) -> str:
        return f"Product(id={self.product_id!r}, name={self.name!r}, vendor={self.vendor!r})"

@dataclass
class RankedCandidate:
    capability: Capability
    topsis_score: float
    semantic_fit: float
    integration_compat: float
    data_readiness: float
    tech_fit: float
    pain_point_match: float
    impl_complexity: ImplComplexity | None = None

    def __repr__(self) -> str:
        return (
            f"RankedCandidate(cap={self.capability.capability_id!r}, "
            f"topsis={self.topsis_score:.3f}, "
            f"dims=[sem={self.semantic_fit:.2f}, "
            f"int={self.integration_compat:.2f}, "
            f"dat={self.data_readiness:.2f}, "
            f"tec={self.tech_fit:.2f}, "
            f"pain={self.pain_point_match:.2f}])"
        )
