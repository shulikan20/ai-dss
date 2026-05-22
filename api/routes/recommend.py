from __future__ import annotations
import os
import sys
import time
import requests as http_requests
from fastapi import APIRouter, HTTPException, Request

from api.constants import DISCLOSURE_TEXT
from api.models import (
    DimensionBreakdownModel,
    ProductDetail,
    QuestionnaireRequest,
    RecommendationItem,
    RecommendationResponse,
)
from api.translator.web_form_translator import WebFormTranslator

router = APIRouter()
_translator = WebFormTranslator()

_MAX_RESULTS = 3 # Max recommendations
_MAX_PRODUCTS = 2
_OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/tags"

_EU_COUNTRIES = frozenset({
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK", "NO", "IS", "LI",
})

def _ping_ollama() -> bool:
    try:
        resp = http_requests.get(_OLLAMA_URL, timeout=2.0)
        return resp.status_code == 200
    except Exception:
        return False

@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    summary="Generate AI tool recommendations for a company",
)
def recommend(
    request: Request,
    body: QuestionnaireRequest,
) -> RecommendationResponse:
    t0 = time.perf_counter()
    repo = request.app.state.repo
    ollama_live = _ping_ollama()
    request.app.state.ollama_available = ollama_live

    try:
        profile = _translator.translate(body, repo)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Could not build a company profile from the submitted form: {exc}",
        ) from exc

    if ollama_live:
        engine = request.app.state.hybrid_engine
        pipeline_used = "hybrid_i2"
    else:
        engine = request.app.state.classical_engine
        pipeline_used = "classical_fallback"

    results = engine.match(profile)
    recommendation_items: list[RecommendationItem] = []
    for result in results[:_MAX_RESULTS]:
        products = repo.get_products(result.capability_id)
        dims = result.dimensions
        recommendation_items.append(
            RecommendationItem(
                rank=result.rank,
                capability_id=result.capability_id,
                capability_name=result.capability_name,
                domain=result.domain,
                topsis_score=round(result.topsis_score, 4),
                explanation=result.explanation or "",
                dimensions=DimensionBreakdownModel(
                    semantic_fit=round(getattr(dims, "semantic_fit", 0.0), 4),
                    integration_compat=round(getattr(dims, "integration_compat", 0.0), 4),
                    data_readiness=round(getattr(dims, "data_readiness", 0.0), 4),
                    tech_fit=round(getattr(dims, "tech_fit", 0.0), 4),
                    pain_point_match=round(getattr(dims, "pain_point_match", 0.0), 4),
                ),
                products=_build_product_list(
                    products,
                    country=getattr(profile, "country", ""),
                ),
            )
        )

    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    return RecommendationResponse(
        company_name=profile.company_name,
        pipeline_used=pipeline_used,  # type: ignore[arg-type]
        llm_available=ollama_live,
        processing_time_ms=elapsed_ms,
        ai_disclosure=DISCLOSURE_TEXT,
        recommendations=recommendation_items,
    )

def _build_product_list(products, country: str = "") -> list[ProductDetail]:
    is_eu = country.upper() in _EU_COUNTRIES
    result = []
    for p in products:
        gdpr_ok = getattr(p, "gdpr_compliant", True)
        if is_eu and not gdpr_ok:
            continue
        result.append(
            ProductDetail(
                product_id=getattr(p, "product_id", ""),
                name=getattr(p, "name", ""),
                vendor=getattr(p, "vendor", ""),
                url=getattr(p, "url", ""),
                cost_tier=getattr(p, "cost_tier", "unknown"),
                has_free_tier=getattr(p, "has_free_tier", False),
                gdpr_compliant=gdpr_ok,
                implementation_effort=getattr(p, "implementation_effort", "medium"),
                cost_notes=getattr(p, "cost_notes", ""),
            )
        )
        if len(result) >= _MAX_PRODUCTS:
            break
    return result