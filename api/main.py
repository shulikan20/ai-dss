from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import CFG
from src.catalog.repository import CatalogRepository
from src.catalog.pg_repository import PostgreSQLCatalogRepository
from src.matching.classical.classical_engine import ClassicalEngine
from src.matching.hybrid.hybrid_engine_v2 import HybridEngineV2  

from api.models import HealthResponse
from api.translator.questions import QUESTION_SCHEMA
from api.database.connection import init_db, get_session_factory
from api.constants import DISCLOSURE_TEXT, PRIVACY_NOTICE, API_VERSION

_ollama_base = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_HEALTH_URL = f"{_ollama_base}/api/tags"
OLLAMA_PING_TIMEOUT_S = 2.0

@asynccontextmanager
async def lifespan(app: FastAPI):
    env = os.environ.get("AIDSS_ENV", "development")
    secret = os.environ.get("SECRET_KEY", "")
    if env == "production" and (
        not secret or secret == "dev-secret-change-in-production"
    ):
        raise RuntimeError(
            "SECRET_KEY must be set to a secure random value in production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    repo = None

    try:
        init_db()
        print("[AI-DSS] Database connected")

        repo = _try_pg_catalog()
        if repo is not None:
            print("[AI-DSS] Catalog: PostgreSQL backend")
        else:
            repo = CatalogRepository()
            repo.__enter__()
            print("[AI-DSS] Catalog: SQLite backend (catalog.db)")

        classical_engine = ClassicalEngine.build(repo=repo)
        hybrid_v2_engine = HybridEngineV2.build(repo=repo, classical_engine=classical_engine)

        app.state.repo = repo
        app.state.engine = hybrid_v2_engine
        app.state.classical_engine = classical_engine
        app.state.ollama_available = _ping_ollama()

        n = len(repo.get_capabilities())
        ollama_msg = "available" if app.state.ollama_available else "offline — classical fallback active"
        print(f"[AI-DSS] Catalog: {n} capabilities")
        print(f"[AI-DSS] Engines ready | Ollama: {ollama_msg}")

    except FileNotFoundError as exc:
        print(f"[AI-DSS] Startup failed — catalog not found: {exc}")
        print(
            "[AI-DSS] Run these first:\n"
            "  python src/tools/build_catalog.py\n"
            "  python scripts/extend_catalog.py\n"
            "  python -m src.catalog.embedder"
        )
        raise

    yield

    if repo is not None:
        repo.__exit__(None, None, None)
        print("[AI-DSS] CatalogRepository closed")

def _try_pg_catalog() -> PostgreSQLCatalogRepository | None:
    try:
        sf = get_session_factory()
        pg_repo = PostgreSQLCatalogRepository(sf)
        count = pg_repo.capability_count()
        if count > 0:
            return pg_repo
        return None
    except Exception:
        return None

_dev_origins = ["http://localhost:3000", "http://localhost:5173"]
ALLOWED_ORIGINS: list[str] = os.environ.get(
    "ALLOWED_ORIGINS", ",".join(_dev_origins)
).split(",")

app = FastAPI(
    title="AI-DSS API",
    description=(
        "AI-powered decision support system — recommends AI tools to "
        "SME e-commerce operators based on their operational profile."
    ),
    version=API_VERSION,
    lifespan=lifespan,
    docs_url=None if os.environ.get("DISABLE_DOCS") == "1" else "/docs",
    redoc_url=None if os.environ.get("DISABLE_DOCS") == "1" else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

from api.routes.recommend import router as recommend_router
app.include_router(recommend_router, prefix="/api", tags=["recommendations"])

from api.routes.catalog import router as catalog_router
app.include_router(catalog_router, prefix="/api", tags=["catalog"])

from api.routes.feedback import router as feedback_router
app.include_router(feedback_router, prefix="/api", tags=["feedback"])

from api.auth.router import router as auth_router
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

from api.auth.oauth import router as oauth_router
app.include_router(oauth_router, prefix="/api/auth", tags=["auth-oauth"])

from api.routes.user import router as user_router
app.include_router(user_router, prefix="/api", tags=["user"])

from api.routes.admin import router as admin_router
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])

from api.routes.translations import router as translations_router
app.include_router(translations_router, prefix="/api", tags=["translations"])

from api.routes.contact import router as contact_router
app.include_router(contact_router, prefix="/api", tags=["contact"])

@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Engine status and catalog info",
)
def health() -> HealthResponse:
    ollama_live = _ping_ollama()
    app.state.ollama_available = ollama_live
    n_caps = app.state.repo.capability_count()
    n_products = app.state.repo.product_count()

    return HealthResponse(
        status="ok",
        ollama_available=ollama_live,
        catalog_capabilities_count=n_caps,
        catalog_products_count=n_products,
        active_llm_model=CFG.LLM_MODEL,
        active_sbert_model=CFG.BI_ENCODER_MODEL,
        version=API_VERSION,
    )

@app.get(
    "/api/questions",
    tags=["questionnaire"],
    summary="Question schema for dynamic form rendering",
)

def get_questions() -> dict:
    return QUESTION_SCHEMA

def _ping_ollama() -> bool:
    try:
        resp = requests.get(OLLAMA_HEALTH_URL, timeout=OLLAMA_PING_TIMEOUT_S)
        return resp.status_code == 200
    except Exception:
        return False