from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class Config:
    # Paths
    DATA_DIR: Path = Path("data")
    PROFILES_DIR: Path = Path("data/profiles")
    CATALOG_DB: Path = Path("src/tools/catalog.db")
    EMBEDDINGS_PATH: Path = Path("src/tools/tool_embeddings.npy")
    SYSTEM_PROMPT: Path = Path("src/matching/llm/prompts/system_prompt.txt")
    # Classical pipeline
    BI_ENCODER_MODEL: str = "all-MiniLM-L6-v2"
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    BI_ENCODER_TOP_K: int = 40
    # TOPSIS weights (must sum to 1.0)
    TOPSIS_WEIGHTS: dict = field(default_factory=lambda: {
        "semantic_fit": 0.35, "integration_compat": 0.25,
        "data_readiness": 0.20, "tech_fit": 0.10, "pain_point_match": 0.10
    })
    # LLM
    LLM_MODEL: str = "llama3.1:8b"
    LLM_BASE_URL: str = "http://localhost:11434"
    # Aggregator
    CLASSICAL_WEIGHT: float = 0.5
    LLM_WEIGHT: float = 0.5
    # Feedback (Product)
    CF_ACTIVATION_THRESHOLD: int = 50  # records before CF activates

CFG = Config()  # single import across all modules
