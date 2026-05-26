from __future__ import annotations

import json
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.auth.dependencies import require_admin
from api.database.connection import get_db
from api.database.models import User

router = APIRouter()

class CapabilityCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    capability_id: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z_]+$")
    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    use_case_category: str = ""
    task_type_target: str = ""
    bottleneck_keywords: list[str] = []
    works_without_data: bool = True
    required_data_types: list[str] = []
    min_history_months_gate: int = 0
    min_technical_capability: int = 1
    mapped_pain_points: list[str] = []
    primary_outcome: str = ""
    secondary_outcomes: list[str] = []
    time_to_value_weeks_min: int | None = None
    time_to_value_weeks_max: int | None = None

class ProductCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str = Field(..., min_length=1, max_length=100)
    capability_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    vendor: str = ""
    url: str = ""
    integrations: list[str] = []
    gdpr_compliant: bool = False
    deployment_model: str = "saas"
    pricing_model: str = "freemium"
    has_free_tier: bool = False
    cost_tier: str = "low"
    cost_notes: str = ""
    implementation_effort: str = "low"
    min_technical_capability: int = 1
    setup_notes: str = ""
    min_history_months: int | None = None
    min_record_count: int | None = None
    works_with_limited_data: bool = True
    data_requirement_notes: str = ""
    notes: str = ""

class CapabilityResponse(BaseModel):
    capability_id: str
    name: str
    domain: str
    description: str
    mapped_pain_points: list[str]
    products_count: int

class AdminStatsResponse(BaseModel):
    capabilities_count: int
    products_count: int
    domains: list[str]
    users_count: int
    sessions_count: int

def _validate_pain_flags(flags: list[str]) -> None:
    for flag in flags:
        parts = flag.split(".")
        if len(parts) != 3:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Invalid pain flag format: '{flag}'. "
                    f"Expected 3 dot-separated parts (domain.section.field_name), "
                    f"got {len(parts)}. Check src/catalog/pain_flags.py for valid constants."
                ),
            )
        if not all(p for p in parts):
            raise HTTPException(
                status_code=422,
                detail=f"Pain flag '{flag}' has empty parts. Each part must be non-empty.",
            )

@router.get("/stats", response_model=AdminStatsResponse, summary="Admin dashboard stats")
def get_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> AdminStatsResponse:
    caps = db.execute(text("SELECT COUNT(*) FROM capabilities")).scalar() or 0
    prods = db.execute(text("SELECT COUNT(*) FROM products")).scalar() or 0
    domains = [
        r[0] for r in db.execute(text("SELECT DISTINCT domain FROM capabilities ORDER BY domain")).all()
    ]
    users = db.execute(text("SELECT COUNT(*) FROM users WHERE deleted_at IS NULL")).scalar() or 0
    sessions = db.execute(text("SELECT COUNT(*) FROM questionnaire_sessions")).scalar() or 0

    return AdminStatsResponse(
        capabilities_count=caps,
        products_count=prods,
        domains=domains,
        users_count=users,
        sessions_count=sessions,
    )

@router.get("/capabilities", summary="List all capabilities with product counts")
def list_capabilities(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> list[CapabilityResponse]:
    rows = db.execute(text("""
        SELECT c.capability_id, c.name, c.domain, c.description, c.mapped_pain_points,
               COALESCE(p.cnt, 0) as products_count
        FROM capabilities c
        LEFT JOIN (SELECT capability_id, COUNT(*) as cnt FROM products GROUP BY capability_id) p
          ON c.capability_id = p.capability_id
        ORDER BY c.domain, c.capability_id
    """)).mappings().all()

    result = []
    for row in rows:
        pain_points = row["mapped_pain_points"]
        if isinstance(pain_points, str):
            pain_points = json.loads(pain_points) if pain_points else []
        elif pain_points is None:
            pain_points = []

        result.append(CapabilityResponse(
            capability_id=row["capability_id"],
            name=row["name"],
            domain=row["domain"],
            description=row["description"] or "",
            mapped_pain_points=pain_points,
            products_count=row["products_count"],
        ))
    return result

@router.post(
    "/capabilities",
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a capability",
)
def upsert_capability(
    body: CapabilityCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    _validate_pain_flags(body.mapped_pain_points)

    from psycopg2.extras import Json

    db.execute(
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
            "capability_id": body.capability_id,
            "name": body.name,
            "domain": body.domain,
            "use_case_category": body.use_case_category,
            "task_type_target": body.task_type_target,
            "description": body.description,
            "bottleneck_keywords": Json(body.bottleneck_keywords),
            "works_without_data": body.works_without_data,
            "required_data_types": Json(body.required_data_types),
            "min_history_months_gate": body.min_history_months_gate,
            "min_technical_capability": body.min_technical_capability,
            "mapped_pain_points": Json(body.mapped_pain_points),
            "primary_outcome": body.primary_outcome,
            "secondary_outcomes": Json(body.secondary_outcomes),
            "time_to_value_weeks_min": body.time_to_value_weeks_min,
            "time_to_value_weeks_max": body.time_to_value_weeks_max,
        },
    )
    return {"detail": f"Capability '{body.capability_id}' saved.", "capability_id": body.capability_id}

@router.post(
    "/products",
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a product",
)
def upsert_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    from psycopg2.extras import Json

    cap = db.execute(
        text("SELECT 1 FROM capabilities WHERE capability_id = :cid"),
        {"cid": body.capability_id},
    ).first()
    if cap is None:
        raise HTTPException(
            status_code=404,
            detail=f"Capability '{body.capability_id}' not found. Create it first.",
        )

    db.execute(
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
            "product_id": body.product_id,
            "capability_id": body.capability_id,
            "name": body.name,
            "vendor": body.vendor,
            "url": body.url,
            "integrations": Json(body.integrations),
            "gdpr_compliant": body.gdpr_compliant,
            "deployment_model": body.deployment_model,
            "pricing_model": body.pricing_model,
            "has_free_tier": body.has_free_tier,
            "cost_tier": body.cost_tier,
            "cost_notes": body.cost_notes,
            "implementation_effort": body.implementation_effort,
            "min_technical_capability": body.min_technical_capability,
            "setup_notes": body.setup_notes,
            "min_history_months": body.min_history_months,
            "min_record_count": body.min_record_count,
            "works_with_limited_data": body.works_with_limited_data,
            "data_requirement_notes": body.data_requirement_notes,
            "notes": body.notes,
        },
    )
    return {"detail": f"Product '{body.product_id}' saved.", "product_id": body.product_id}

@router.delete(
    "/capabilities/{capability_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a capability and its products",
)
def delete_capability(
    capability_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> None:
    existing = db.execute(
        text("SELECT 1 FROM capabilities WHERE capability_id = :cid"),
        {"cid": capability_id},
    ).first()
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Capability '{capability_id}' not found.")

    db.execute(
        text("DELETE FROM products WHERE capability_id = :cid"),
        {"cid": capability_id},
    )
    db.execute(
        text("DELETE FROM capabilities WHERE capability_id = :cid"),
        {"cid": capability_id},
    )

