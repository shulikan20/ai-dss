from __future__ import annotations
import os
import time
import requests as http_requests
import dataclasses, json
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi import Depends

from api.auth.dependencies import get_current_user_optional
from api.database.connection import get_db
from api.database.models import User
from api.database.repository import SessionRepository, UserRepository
from api.constants import DISCLOSURE_TEXT
from api.models import (
    DimensionBreakdownModel,
    ProductDetail,
    QuestionnaireRequest,
    RecommendationItem,
    RecommendationResponse,
)
from api.translator.web_form_translator import WebFormTranslator
from config import CFG

router = APIRouter()
_translator = WebFormTranslator()

def _valid_pain_flags() -> frozenset[str]:
    global _VALID_PAIN_FLAGS
    try:
        return _VALID_PAIN_FLAGS
    except NameError:
        from src.catalog.pain_flags import PainFlags
        _VALID_PAIN_FLAGS = frozenset(PainFlags.all_paths())
        return _VALID_PAIN_FLAGS

_MAX_RESULTS = 5 # Max recommendations
_MAX_PRODUCTS = 2
_EXPLAIN_TOP_N = 3
_OLLAMA_BASE = os.environ.get("OLLAMA_URL", "http://localhost:11434")
_OLLAMA_URL = _OLLAMA_BASE + "/api/tags"

_EU_COUNTRIES = frozenset({
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK", "NO", "IS", "LI",
})

_EXPLAIN_SYSTEM = """\
You write short, specific explanations of why an AI tool helps a particular company.
Each explanation must be exactly 2 sentences. Be concrete — mention the company's \
actual problem. Do not start with "This tool" or "I recommend". \
Return ONLY a JSON object mapping capability_id to your 2-sentence explanation."""

_LANGUAGE_INSTRUCTIONS = {
    "de": (
        "Write all explanations in German (natural Austrian/German business "
        "language, formal 'Sie'). Keep the JSON keys (capability_id) in English."
    ),
}

@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    summary="Generate AI tool recommendations for a company",
)
def recommend(
    request: Request,
    body: QuestionnaireRequest,
    pipeline: str | None = None,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
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
    
    if body.export_enrichment:
        base = (profile.bottleneck_description or "").rstrip()
        profile.bottleneck_description = (base + "\n\n" + body.export_enrichment.strip()).strip()
    if body.export_pain_flags:
        _valid = _valid_pain_flags()
        for flag, conf in body.export_pain_flags.items():
            if flag in _valid and isinstance(conf, (int, float)) and conf >= 0.7:
                profile.pain_point_flags[flag] = True

    engines = getattr(request.app.state, "engines", {})
    default_mode = getattr(request.app.state, "pipeline_mode", "hybrid")
    mode = pipeline if pipeline in ("hybrid", "llm", "classical") else default_mode

    if not ollama_live and mode in ("llm", "hybrid"):
        engine = engines.get("classical", request.app.state.engine)
        pipeline_used = "classical_fallback"
    elif mode == "classical":
        engine = engines.get("classical", request.app.state.engine)
        pipeline_used = "classical_fallback"
    else:
        engine = engines.get(mode, request.app.state.engine)
        pipeline_used = {"llm": "llm", "hybrid": "i3_llm_semantic"}[mode]

    results = engine.match(profile)

    recommendation_id = None
    try:
        session_repo = SessionRepository(db)
        company_id = None
        if current_user is not None:
            user_repo = UserRepository(db)
            company = user_repo.get_or_create_company(
                company_name=body.company_name,
                country=body.country,
                user_id=current_user.id,
            )
            company_id = company.id
        
        saved = session_repo.save(
            tier=body.tier,
            domains=body.domains,
            bottleneck_text=body.bottleneck_text,
            answers=body.answers if hasattr(body, "answers") else {},
            profile_snapshot=dataclasses.asdict(profile),
            pipeline_used=pipeline_used,
            llm_available=ollama_live,
            processing_time_ms=int((time.perf_counter() - t0) * 1000),
            ranked_results=[dataclasses.asdict(r) for r in results],
            company_id=company_id,
        )
        recommendation_id = str(saved.recommendation_id)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Failed to persist session")

    language = (
        getattr(current_user, "language_preference", None)
        or _accept_language_primary(request.headers.get("accept-language"))
        or "en"
    )
    llm_explanations: dict[str, str] = {}
    if ollama_live:
        llm_explanations = _generate_explanations(
            profile, results[:_EXPLAIN_TOP_N], repo, language=language
        )

    recommendation_items: list[RecommendationItem] = []
    for result in results[:_MAX_RESULTS]:
        products = repo.get_products(result.capability_id)
        dims = result.dimensions
        explanation = llm_explanations.get(result.capability_id) or result.explanation or ""
        recommendation_items.append(
            RecommendationItem(
                rank=result.rank,
                capability_id=result.capability_id,
                capability_name=result.capability_name,
                domain=result.domain,
                topsis_score=round(result.topsis_score, 4),
                explanation=explanation,
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
                    profile=profile,
                    team_size=getattr(body, "team_size", None),
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
        recommendation_id=recommendation_id,
        recommendations=recommendation_items,
    )

def _language_instruction(language: str | None) -> str:
    if not language or language == "en":
        return ""
    return _LANGUAGE_INSTRUCTIONS.get(language, "")


def _accept_language_primary(header: str | None) -> str | None:
    if not header:
        return None
    first = header.split(",")[0].strip()
    if not first or first == "*":
        return None
    return first.split("-")[0].split(";")[0].strip().lower() or None

def _ping_ollama() -> bool:
    try:
        resp = http_requests.get(_OLLAMA_URL, timeout=2.0)
        return resp.status_code == 200
    except Exception:
        return False

def _generate_explanations(
    profile,
    top_results: list,
    repo,
    language: str = "en",
) -> dict[str, str]:
    if not top_results:
        return {}

    cap_map = {c.capability_id: c for c in repo.get_capabilities()}

    team_size = getattr(profile, "team_size", None)
    company_bits = [profile.company_name or "Company"]
    if team_size:
        company_bits.append(f"{team_size} people")
    if profile.country:
        company_bits.append(profile.country)

    confirmed_pain_labels = [
        k.split(".")[-1].replace("pain_", "").replace("_", " ")
        for k, v in profile.pain_point_flags.items() if v
    ]
    pains = ", ".join(confirmed_pain_labels) if confirmed_pain_labels else "none stated"

    bottleneck = profile.bottleneck_description or "(no bottleneck text provided)"

    tool_lines = []
    for r in top_results:
        cap = cap_map.get(r.capability_id)
        desc = cap.description if cap else ""
        name = cap.name if cap else r.capability_name
        tool_lines.append(f"- {r.capability_id}: {name} — {desc}")

    user_prompt = (
        f"Company: {', '.join(company_bits)}\n"
        f"Key pain points: {pains}\n"
        f'Problem described: "{bottleneck}"\n\n'
        f"Write a 2-sentence explanation for each tool:\n"
        + "\n".join(tool_lines)
        + '\n\nReturn JSON only: {"capability_id": "2-sentence explanation", ...}'
    )

    system_prompt = _EXPLAIN_SYSTEM
    lang_line = _language_instruction(language)
    if lang_line:
        system_prompt = f"{system_prompt}\n{lang_line}"

    try:
        resp = http_requests.post(
            _OLLAMA_BASE.rstrip("/") + "/api/generate",
            json={
                "model": CFG.LLM_MODEL,
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False,
                "options": {"temperature": 0.3},
            },
            timeout=getattr(CFG, "LLM_TIMEOUT_SEC", 120),
        )
        resp.raise_for_status()
        raw = resp.json()["response"].strip()
    except Exception:
        return {}

    return _parse_explanations(raw, {r.capability_id for r in top_results})


def _parse_explanations(raw: str, valid_ids: set[str]) -> dict[str, str]:
    clean = raw.strip()
    if "```" in clean:
        clean = "\n".join(
            ln for ln in clean.split("\n") if not ln.strip().startswith("```")
        ).strip()

    start = clean.find("{")
    end = clean.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    try:
        parsed = json.loads(clean[start : end + 1])
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}

    out: dict[str, str] = {}
    for cap_id, text in parsed.items():
        if cap_id in valid_ids and isinstance(text, str) and text.strip():
            out[cap_id] = text.strip()
    return out


def _build_product_list(
    products,
    country: str = "",
    profile=None,
    team_size: str | None = None,
) -> list[ProductDetail]:
    is_eu = country.upper() in _EU_COUNTRIES
    eligible = [
        p for p in products
        if not (is_eu and not getattr(p, "gdpr_compliant", True))
    ]

    fit_by_id: dict[int, tuple[float, bool]] = {}
    if profile is not None and eligible:
        from api.tools.product_scorer import score_products_for_profile

        scored = score_products_for_profile(eligible, profile, team_size=team_size)
        eligible = [s.product for s in scored]
        fit_by_id = {id(s.product): (s.fit_score, s.best_fit) for s in scored}

    result = []
    for p in eligible[:_MAX_PRODUCTS]:
        fit_score, best_fit = fit_by_id.get(id(p), (None, False))
        result.append(
            ProductDetail(
                product_id=getattr(p, "product_id", ""),
                name=getattr(p, "name", ""),
                vendor=getattr(p, "vendor", ""),
                url=getattr(p, "url", ""),
                cost_tier=getattr(p, "cost_tier", "unknown"),
                has_free_tier=getattr(p, "has_free_tier", False),
                gdpr_compliant=getattr(p, "gdpr_compliant", True),
                implementation_effort=getattr(p, "implementation_effort", "medium"),
                cost_notes=getattr(p, "cost_notes", ""),
                price_tier=getattr(p, "price_tier", None),
                platform_integrations=getattr(p, "platform_integrations", None),
                company_size_fit=getattr(p, "company_size_fit", None),
                setup_complexity=getattr(p, "setup_complexity", None),
                fit_score=fit_score,
                best_fit=best_fit,
            )
        )
    return result