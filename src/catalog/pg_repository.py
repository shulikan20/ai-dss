from __future__ import annotations
import json
from typing import Any
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from src.models.catalog_item import Capability, Product

class PostgreSQLCatalogRepository:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> PostgreSQLCatalogRepository:
        return self

    def __exit__(self, *_: Any) -> None:
        pass

    def close(self) -> None:
        pass

    def get_capabilities(self, domain: str | None = None) -> list[Capability]:
        with self._session_factory() as db:
            if domain:
                rows = db.execute(
                    text("SELECT * FROM capabilities WHERE domain = :domain ORDER BY capability_id"),
                    {"domain": domain},
                ).mappings().all()
            else:
                rows = db.execute(
                    text("SELECT * FROM capabilities ORDER BY domain, capability_id")
                ).mappings().all()

            if not rows:
                return []

            capabilities = [self._row_to_capability(dict(r)) for r in rows]
            cap_ids = [c.capability_id for c in capabilities]
            prod_rows = db.execute(
                text(
                    "SELECT capability_id, integrations FROM products "
                    "WHERE capability_id = ANY(:ids)"
                ),
                {"ids": cap_ids},
            ).mappings().all()

            integrations_map: dict[str, set[str]] = {cid: set() for cid in cap_ids}
            for row in prod_rows:
                cid = row["capability_id"]
                ints = row["integrations"]
                if isinstance(ints, list):
                    integrations_map[cid].update(str(i).lower() for i in ints)
                elif isinstance(ints, str):
                    try:
                        parsed = json.loads(ints)
                        if isinstance(parsed, list):
                            integrations_map[cid].update(str(i).lower() for i in parsed)
                    except (json.JSONDecodeError, TypeError):
                        pass

            for cap in capabilities:
                cap.available_integrations = sorted(integrations_map[cap.capability_id])

            return capabilities

    def get_products(self, capability_id: str) -> list[Product]:
        with self._session_factory() as db:
            rows = db.execute(
                text("SELECT * FROM products WHERE capability_id = :cid ORDER BY product_id"),
                {"cid": capability_id},
            ).mappings().all()
            return [self._row_to_product(dict(r)) for r in rows]
        
    def get_all_products(self) -> list[Product]:
        with self._session_factory() as db:
            rows = db.execute(
                text("SELECT * FROM products ORDER BY capability_id, product_id")
            ).mappings().all()
            return [self._row_to_product(dict(r)) for r in rows]

    def get_mapped_pain_points(self, capability_id: str) -> list[str]:
        with self._session_factory() as db:
            row = db.execute(
                text("SELECT mapped_pain_points FROM capabilities WHERE capability_id = :cid"),
                {"cid": capability_id},
            ).mappings().first()
            if not row:
                return []
            val = row["mapped_pain_points"]
            if isinstance(val, list):
                return [str(x) for x in val]
            if isinstance(val, str):
                try:
                    parsed = json.loads(val)
                    return [str(x) for x in parsed] if isinstance(parsed, list) else []
                except (json.JSONDecodeError, TypeError):
                    return []
            return []

    def get_capability_ids_with_products(self) -> set[str]:
        with self._session_factory() as db:
            rows = db.execute(
                text("SELECT DISTINCT capability_id FROM products")
            ).all()
            return {row[0] for row in rows}

    def get_gdpr_capable_capability_ids(self) -> set[str]:
        with self._session_factory() as db:
            rows = db.execute(
                text("SELECT DISTINCT capability_id FROM products WHERE gdpr_compliant = true")
            ).all()
            return {row[0] for row in rows}

    def has_gdpr_product(self, capability_id: str) -> bool:
        with self._session_factory() as db:
            row = db.execute(
                text("SELECT COUNT(*) FROM products WHERE capability_id = :cid AND gdpr_compliant = true"),
                {"cid": capability_id},
            ).scalar()
            return (row or 0) > 0

    def get_all_domains(self) -> list[str]:
        with self._session_factory() as db:
            rows = db.execute(
                text("SELECT DISTINCT domain FROM capabilities ORDER BY domain")
            ).all()
            return [row[0] for row in rows]

    def capability_count(self) -> int:
        with self._session_factory() as db:
            return db.execute(text("SELECT COUNT(*) FROM capabilities")).scalar() or 0

    def product_count(self) -> int:
        with self._session_factory() as db:
            return db.execute(text("SELECT COUNT(*) FROM products")).scalar() or 0

    @staticmethod
    def _row_to_capability(row: dict[str, Any]) -> Capability:
        def _ensure_list(val: Any) -> list[str]:
            if isinstance(val, list):
                return [str(x) for x in val]
            if isinstance(val, str):
                try:
                    parsed = json.loads(val)
                    return [str(x) for x in parsed] if isinstance(parsed, list) else []
                except (json.JSONDecodeError, TypeError):
                    return []
            return []

        return Capability(
            capability_id=str(row["capability_id"]),
            name=str(row["name"]),
            domain=str(row["domain"]),
            use_case_category=str(row.get("use_case_category") or ""),
            task_type_target=str(row.get("task_type_target") or ""),
            description=str(row.get("description") or ""),
            bottleneck_keywords=_ensure_list(row.get("bottleneck_keywords")),
            works_without_data=bool(row.get("works_without_data", True)),
            required_data_types=_ensure_list(row.get("required_data_types")),
            min_history_months_gate=int(row.get("min_history_months_gate") or 0),
            min_technical_capability=int(row.get("min_technical_capability") or 1),
            available_integrations=[],
            mapped_pain_points=_ensure_list(row.get("mapped_pain_points")),
            primary_outcome=str(row.get("primary_outcome") or ""),
            secondary_outcomes=_ensure_list(row.get("secondary_outcomes")),
            time_to_value_weeks_min=(
                int(row["time_to_value_weeks_min"])
                if row.get("time_to_value_weeks_min") is not None else None
            ),
            time_to_value_weeks_max=(
                int(row["time_to_value_weeks_max"])
                if row.get("time_to_value_weeks_max") is not None else None
            ),
            browse_category=(
                str(row["browse_category"]) if row.get("browse_category") else None
            ),
        )

    @staticmethod
    def _row_to_product(row: dict[str, Any]) -> Product:
        def _ensure_list(val: Any) -> list[str]:
            if isinstance(val, list):
                return [str(x) for x in val]
            if isinstance(val, str):
                try:
                    parsed = json.loads(val)
                    return [str(x) for x in parsed] if isinstance(parsed, list) else []
                except (json.JSONDecodeError, TypeError):
                    return []
            return []

        return Product(
            product_id=str(row["product_id"]),
            capability_id=str(row["capability_id"]),
            name=str(row["name"]),
            vendor=str(row.get("vendor") or ""),
            url=str(row.get("url") or ""),
            integrations=_ensure_list(row.get("integrations")),
            gdpr_compliant=bool(row.get("gdpr_compliant", False)),
            deployment_model=str(row.get("deployment_model") or "saas"),
            pricing_model=str(row.get("pricing_model") or "freemium"),
            has_free_tier=bool(row.get("has_free_tier", False)),
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
            works_with_limited_data=bool(row.get("works_with_limited_data", True)),
            data_requirement_notes=str(row.get("data_requirement_notes") or ""),
            setup_notes=str(row.get("setup_notes") or ""),
            notes=str(row.get("notes") or ""),
            price_tier=str(row["price_tier"]) if row.get("price_tier") else None,
            platform_integrations=(
                _ensure_list(row["platform_integrations"])
                if row.get("platform_integrations") else None
            ),
            company_size_fit=(
                str(row["company_size_fit"]) if row.get("company_size_fit") else None
            ),
            setup_complexity=(
                str(row["setup_complexity"]) if row.get("setup_complexity") else None
            ),
        )
