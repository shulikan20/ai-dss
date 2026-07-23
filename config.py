from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).parent.resolve()

@dataclass
class Config:
    ROOT_DIR: Path = ROOT
    DATA_DIR: Path = ROOT / "data"
    PROFILES_DIR: Path = ROOT / "data" / "profiles"
    EXPORTS_DIR: Path = ROOT / "data" / "exports"
    SCHEMA_DIR: Path = ROOT / "data" / "schema"
    RESULTS_DIR: Path = ROOT / "results"
    CATALOG_DB: Path = ROOT / "src" / "tools" / "catalog.db"
    EMBEDDINGS_PATH: Path = ROOT / "src" / "tools" / "tool_embeddings.npy"
    SCHEMA_PATH: Path = ROOT / "data" / "schema" / "company_profile_schema.json"
    QUESTIONNAIRE: Path = ROOT / "data" / "questionnaire.json"
    SYSTEM_PROMPT: Path = ROOT / "src" / "matching" / "llm" / "prompts" / "system_prompt.txt"
    BI_ENCODER_MODEL: str = "multi-qa-MiniLM-L6-cos-v1"
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    BI_ENCODER_TOP_K: int = 40
    LLM_MODEL: str = field(default_factory=lambda: os.environ.get("LLM_MODEL", "phi4"))
    LLM_BASE_URL: str = "http://localhost:11434"
    LLM_TIMEOUT_SEC: int = field(
        default_factory=lambda: int(os.environ.get("LLM_TIMEOUT_SEC", "300"))
    )
    USE_LLM_ENRICHMENT: bool = True
    TOPSIS_WEIGHTS: dict = field(default_factory=lambda: {
        "semantic_fit": 0.35,
        "integration_compat": 0.05,
        "data_readiness": 0.20,
        "tech_fit": 0.10,
        "pain_point_match": 0.30,
    })
    TOPSIS_FIXED_REFERENCE: bool = True
    CLASSICAL_WEIGHT: float = 0.5
    LLM_WEIGHT: float = 0.5
    CF_ACTIVATION_THRESHOLD: int = 50

    def __post_init__(self) -> None:
        total = sum(self.TOPSIS_WEIGHTS.values())
        if abs(total - 1.0) > 1e-9:
            raise ValueError(
                f"TOPSIS_WEIGHTS must sum to 1.0, got {total:.4f}. "
                f"Current weights: {self.TOPSIS_WEIGHTS}"
            )

CFG = Config()