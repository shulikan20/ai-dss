from __future__ import annotations
from typing import Annotated, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

class HealthResponse(BaseModel):
    """GET /api/health"""
    model_config = ConfigDict(frozen=True)
    status: str
    ollama_available: bool
    catalog_capabilities_count: int
    catalog_products_count: int
    active_llm_model: str
    active_sbert_model: str
    version: str

class QuestionnaireRequest(BaseModel):
    """POST /api/recommend request body."""
    model_config = ConfigDict(str_strip_whitespace=True)
    tier: Literal["quick", "standard", "full"]
    company_name: Annotated[str, Field(min_length=1, max_length=200)]
    country: Annotated[str, Field(min_length=2, max_length=2)]
    team_size: Optional[str] = None
    domains: Annotated[list[str], Field(min_length=1)]
    bottleneck_text: Annotated[str, Field(min_length=20, max_length=2000)]
    answers: dict[str, str] = Field(default_factory=dict)

    @field_validator("country")
    @classmethod
    def country_uppercase(cls, v: str) -> str:
        return v.upper()

    @field_validator("domains")
    @classmethod
    def domains_valid(cls, v: list[str]) -> list[str]:
        allowed = {
            "ecommerce_ops",
            "customer_support",
            "marketing",
            "supply_chain",
            "crm_sales",
            "operations_backoffice",
        }
        invalid = set(v) - allowed
        if invalid:
            raise ValueError(f"Unknown domains: {invalid}. Allowed: {allowed}")
        return v

class DimensionBreakdownModel(BaseModel):
    model_config = ConfigDict(frozen=True)
    semantic_fit: float
    integration_compat: float
    data_readiness: float
    tech_fit: float
    pain_point_match: float

class ProductDetail(BaseModel):
    model_config = ConfigDict(frozen=True)
    product_id: str
    name: str
    vendor: str
    url: str
    cost_tier: str
    has_free_tier: bool
    gdpr_compliant: bool
    implementation_effort: str
    cost_notes: str = ""

class RecommendationItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    rank: int
    capability_id: str
    capability_name: str
    domain: str
    topsis_score: float
    explanation: str
    dimensions: DimensionBreakdownModel
    products: list[ProductDetail]

class RecommendationResponse(BaseModel):
    """POST /api/recommend response."""
    model_config = ConfigDict(frozen=True)
    company_name: str
    pipeline_used: Literal["hybrid_i2", "classical_fallback"]
    llm_available: bool
    processing_time_ms: int
    ai_disclosure: str
    recommendations: list[RecommendationItem]

class CatalogCapabilityModel(BaseModel):
    """GET /api/catalog response."""
    model_config = ConfigDict(frozen=True)
    capability_id: str
    name: str
    domain: str
    description: str
    primary_outcome: str

class CatalogResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    capabilities: list[CatalogCapabilityModel]
    total: int

class UserCreate(BaseModel):
    """POST /api/auth/register request."""
    email: Annotated[str, Field(min_length=5, max_length=255)]
    password: Annotated[str, Field(min_length=8, max_length=128)]
    company_name: Annotated[str, Field(min_length=1, max_length=200)]
    country: Annotated[str, Field(min_length=2, max_length=2)]

    @field_validator("email")
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("country")
    @classmethod
    def country_uppercase(cls, v: str) -> str:
        return v.upper()


class UserLogin(BaseModel):
    """POST /api/auth/login request."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """POST /api/auth/login response."""
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class UserProfile(BaseModel):
    """GET /api/me response."""
    model_config = ConfigDict(frozen=True)
    user_id: str
    email: str
    company_name: str
    country: str
    recommendations_count: int = 0

class ExportMetrics(BaseModel):
    export_type: str
    metrics: dict[str, float | int | str]
    pain_flags_inferred: dict[str, bool]
    summary_text: str