#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from api.database.connection import get_engine

def main() -> None:
    catalog_path = ROOT / "src" / "tools" / "catalog.db"
    if not catalog_path.exists():
        print(f"[ERROR] catalog.db not found at {catalog_path}")
        print("Run: python src/tools/build_catalog.py && python scripts/extend_catalog.py")
        sys.exit(1)

    target_url = os.environ.get("DATABASE_URL", "postgresql://aidss:aidss@localhost:5432/aidss")
    display_url = target_url
    if "@" in target_url:
        prefix, rest = target_url.split("@", 1)
        if ":" in prefix.split("//", 1)[-1]:
            user_part = prefix.rsplit(":", 1)[0]
            display_url = f"{user_part}:***@{rest}"
    print(f"[Target DB] {display_url}")

    engine = get_engine()
    _ensure_catalog_tables(engine)

    sqlite_conn = sqlite3.connect(str(catalog_path))
    sqlite_conn.row_factory = sqlite3.Row

    sqlite_caps = sqlite_conn.execute(
        "SELECT * FROM capabilities ORDER BY domain, capability_id"
    ).fetchall()
    sqlite_prods = sqlite_conn.execute(
        "SELECT * FROM products ORDER BY capability_id, product_id"
    ).fetchall()
    sqlite_conn.close()

    print(f"[SQLite] Read {len(sqlite_caps)} capabilities, {len(sqlite_prods)} products")

    with engine.begin() as conn:
        for row in sqlite_caps:
            row = dict(row)
            conn.execute(
                text("""
                    INSERT INTO capabilities (
                        capability_id, name, domain, use_case_category,
                        task_type_target, description, bottleneck_keywords,
                        works_without_data, required_data_types,
                        min_history_months_gate, min_technical_capability,
                        mapped_pain_points, primary_outcome, secondary_outcomes,
                        time_to_value_weeks_min, time_to_value_weeks_max
                    ) VALUES (
                        :capability_id, :name, :domain, :use_case_category,
                        :task_type_target, :description, :bottleneck_keywords,
                        :works_without_data, :required_data_types,
                        :min_history_months_gate, :min_technical_capability,
                        :mapped_pain_points, :primary_outcome, :secondary_outcomes,
                        :time_to_value_weeks_min, :time_to_value_weeks_max
                    )
                    ON CONFLICT (capability_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        domain = EXCLUDED.domain,
                        use_case_category = EXCLUDED.use_case_category,
                        task_type_target = EXCLUDED.task_type_target,
                        description = EXCLUDED.description,
                        bottleneck_keywords = EXCLUDED.bottleneck_keywords,
                        works_without_data = EXCLUDED.works_without_data,
                        required_data_types = EXCLUDED.required_data_types,
                        min_history_months_gate = EXCLUDED.min_history_months_gate,
                        min_technical_capability = EXCLUDED.min_technical_capability,
                        mapped_pain_points = EXCLUDED.mapped_pain_points,
                        primary_outcome = EXCLUDED.primary_outcome,
                        secondary_outcomes = EXCLUDED.secondary_outcomes,
                        time_to_value_weeks_min = EXCLUDED.time_to_value_weeks_min,
                        time_to_value_weeks_max = EXCLUDED.time_to_value_weeks_max
                """),
                {
                    "capability_id": row["capability_id"],
                    "name": row["name"],
                    "domain": row["domain"],
                    "use_case_category": row.get("use_case_category"),
                    "task_type_target": row.get("task_type_target"),
                    "description": row.get("description"),
                    "bottleneck_keywords": _json_str_to_jsonb(row.get("bottleneck_keywords")),
                    "works_without_data": bool(int(row.get("works_without_data") or 1)),
                    "required_data_types": _json_str_to_jsonb(row.get("required_data_types")),
                    "min_history_months_gate": int(row.get("min_history_months_gate") or 0),
                    "min_technical_capability": int(row.get("min_technical_capability") or 1),
                    "mapped_pain_points": _json_str_to_jsonb(row.get("mapped_pain_points")),
                    "primary_outcome": row.get("primary_outcome"),
                    "secondary_outcomes": _json_str_to_jsonb(row.get("secondary_outcomes")),
                    "time_to_value_weeks_min": row.get("time_to_value_weeks_min"),
                    "time_to_value_weeks_max": row.get("time_to_value_weeks_max"),
                },
            )
        for row in sqlite_prods:
            row = dict(row)
            conn.execute(
                text("""
                    INSERT INTO products (
                        product_id, capability_id, name, vendor, url,
                        integrations, gdpr_compliant, deployment_model,
                        pricing_model, has_free_tier, cost_tier, cost_notes,
                        implementation_effort, min_technical_capability,
                        setup_notes, min_history_months, min_record_count,
                        works_with_limited_data, data_requirement_notes, notes
                    ) VALUES (
                        :product_id, :capability_id, :name, :vendor, :url,
                        :integrations, :gdpr_compliant, :deployment_model,
                        :pricing_model, :has_free_tier, :cost_tier, :cost_notes,
                        :implementation_effort, :min_technical_capability,
                        :setup_notes, :min_history_months, :min_record_count,
                        :works_with_limited_data, :data_requirement_notes, :notes
                    )
                    ON CONFLICT (product_id) DO UPDATE SET
                        capability_id = EXCLUDED.capability_id,
                        name = EXCLUDED.name,
                        vendor = EXCLUDED.vendor,
                        url = EXCLUDED.url,
                        integrations = EXCLUDED.integrations,
                        gdpr_compliant = EXCLUDED.gdpr_compliant,
                        deployment_model = EXCLUDED.deployment_model,
                        pricing_model = EXCLUDED.pricing_model,
                        has_free_tier = EXCLUDED.has_free_tier,
                        cost_tier = EXCLUDED.cost_tier,
                        cost_notes = EXCLUDED.cost_notes,
                        implementation_effort = EXCLUDED.implementation_effort,
                        min_technical_capability = EXCLUDED.min_technical_capability,
                        setup_notes = EXCLUDED.setup_notes,
                        min_history_months = EXCLUDED.min_history_months,
                        min_record_count = EXCLUDED.min_record_count,
                        works_with_limited_data = EXCLUDED.works_with_limited_data,
                        data_requirement_notes = EXCLUDED.data_requirement_notes,
                        notes = EXCLUDED.notes
                """),
                {
                    "product_id": row["product_id"],
                    "capability_id": row["capability_id"],
                    "name": row["name"],
                    "vendor": row.get("vendor"),
                    "url": row.get("url"),
                    "integrations": _json_str_to_jsonb(row.get("integrations")),
                    "gdpr_compliant": bool(int(row.get("gdpr_compliant") or 0)),
                    "deployment_model": row.get("deployment_model"),
                    "pricing_model": row.get("pricing_model"),
                    "has_free_tier": bool(int(row.get("has_free_tier") or 0)),
                    "cost_tier": row.get("cost_tier"),
                    "cost_notes": row.get("cost_notes"),
                    "implementation_effort": row.get("implementation_effort"),
                    "min_technical_capability": int(row.get("min_technical_capability") or 1),
                    "setup_notes": row.get("setup_notes"),
                    "min_history_months": row.get("min_history_months"),
                    "min_record_count": row.get("min_record_count"),
                    "works_with_limited_data": bool(int(row.get("works_with_limited_data") or 1)),
                    "data_requirement_notes": row.get("data_requirement_notes"),
                    "notes": row.get("notes"),
                },
            )
    with engine.connect() as conn:
        pg_caps = conn.execute(text("SELECT COUNT(*) FROM capabilities")).scalar()
        pg_prods = conn.execute(text("SELECT COUNT(*) FROM products")).scalar()

    print(f"[PostgreSQL] {pg_caps} capabilities, {pg_prods} products")

    if pg_caps == len(sqlite_caps) and pg_prods == len(sqlite_prods):
        print("[OK] Row counts match — migration successful")
    else:
        print(f"[WARNING] Row count mismatch! SQLite: {len(sqlite_caps)}/{len(sqlite_prods)}, PG: {pg_caps}/{pg_prods}")
        sys.exit(1)

def _ensure_catalog_tables(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS capabilities (
                capability_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                domain VARCHAR(100) NOT NULL,
                use_case_category VARCHAR(100),
                task_type_target VARCHAR(50),
                description TEXT,
                bottleneck_keywords JSONB,
                works_without_data BOOLEAN NOT NULL DEFAULT true,
                required_data_types JSONB,
                min_history_months_gate INTEGER NOT NULL DEFAULT 0,
                min_technical_capability INTEGER NOT NULL DEFAULT 1,
                mapped_pain_points JSONB,
                primary_outcome TEXT,
                secondary_outcomes JSONB,
                time_to_value_weeks_min INTEGER,
                time_to_value_weeks_max INTEGER,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                product_id VARCHAR(100) PRIMARY KEY,
                capability_id VARCHAR(100) NOT NULL
                    REFERENCES capabilities(capability_id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                vendor VARCHAR(255),
                url VARCHAR(500),
                integrations JSONB,
                gdpr_compliant BOOLEAN NOT NULL DEFAULT false,
                deployment_model VARCHAR(50),
                pricing_model VARCHAR(50),
                has_free_tier BOOLEAN NOT NULL DEFAULT false,
                cost_tier VARCHAR(50),
                cost_notes TEXT,
                implementation_effort VARCHAR(50),
                min_technical_capability INTEGER NOT NULL DEFAULT 1,
                setup_notes TEXT,
                min_history_months INTEGER,
                min_record_count INTEGER,
                works_with_limited_data BOOLEAN NOT NULL DEFAULT true,
                data_requirement_notes TEXT,
                notes TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """))
    print("[Tables] capabilities and products ready")

def _json_str_to_jsonb(val: str | None):
    from psycopg2.extras import Json

    if not val:
        return None
    try:
        parsed = json.loads(val)
        return Json(parsed)
    except (json.JSONDecodeError, TypeError):
        return None

if __name__ == "__main__":
    main()
