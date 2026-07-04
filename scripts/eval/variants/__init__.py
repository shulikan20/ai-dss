from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from src.matching.base import BaseMatchEngine
    from src.models.company_profile import CompanyProfile
    from src.models.recommendation import ClassicalResult

@dataclass
class VariantContext:
    hybrid_engine: "BaseMatchEngine | None" = None
    classical_engine: "BaseMatchEngine | None" = None
    repo: object | None = None

    def get_repo(self) -> object:
        if self.repo is None:
            self.repo = _build_repo()
        return self.repo

    def get_hybrid(self) -> "BaseMatchEngine":
        if self.hybrid_engine is None:
            from src.matching.hybrid.hybrid_engine import HybridEngine

            self.hybrid_engine = HybridEngine.build(repo=self.get_repo())
        return self.hybrid_engine

    def get_classical(self) -> "BaseMatchEngine":
        if self.classical_engine is None:
            from src.matching.classical.classical_engine import ClassicalEngine

            self.classical_engine = ClassicalEngine.build(repo=self.get_repo())
        return self.classical_engine


def _build_repo() -> object:
    try:
        from api.database.connection import get_session_factory
        from src.catalog.pg_repository import PostgreSQLCatalogRepository

        repo = PostgreSQLCatalogRepository(get_session_factory())
        if repo.capability_count() > 0:
            return repo
    except Exception:  # noqa
        pass

    import atexit

    from src.catalog.repository import CatalogRepository

    repo = CatalogRepository()
    repo.__enter__()
    atexit.register(repo.close)
    return repo


class VariantEngine(ABC):
    name: ClassVar[str]
    description: ClassVar[str]
    pipeline_label: ClassVar[str] = "classical_fallback"

    def __init__(self, ctx: VariantContext) -> None:
        self.ctx = ctx

    @abstractmethod
    def match(self, profile: "CompanyProfile") -> "list[ClassicalResult]":
        """Run the variant pipeline and return a ranked result list."""


_REGISTRY: dict[str, type[VariantEngine]] = {}
_PENDING: frozenset[str] = frozenset(
    {"v3_soft_flags", "v5_better_prompt", "v6_confidence"}
)


def register(cls: type[VariantEngine]) -> type[VariantEngine]:
    name = getattr(cls, "name", None)
    if not name:
        raise ValueError(f"{cls.__name__} must define a non-empty 'name'")
    if name in _REGISTRY and _REGISTRY[name] is not cls:
        raise ValueError(f"Duplicate variant name '{name}' ({cls.__name__})")
    _REGISTRY[name] = cls
    return cls


def get_variant(name: str, ctx: VariantContext | None = None) -> VariantEngine:
    cls = _REGISTRY.get(name)
    if cls is None:
        if name in _PENDING:
            raise NotImplementedError(
                f"Variant '{name}' is planned for Phase H5 but not yet "
                f"implemented. Implement a variant in scripts/eval/variants and @register it."
            )
        raise KeyError(
            f"Unknown algorithm variant '{name}'. "
            f"Available: {sorted(_REGISTRY)}"
        )
    return cls(ctx if ctx is not None else VariantContext())


def available_variants() -> dict[str, str]:
    return {name: cls.description for name, cls in sorted(_REGISTRY.items())}

from . import v1_baseline, v2_classical  # noqa
from . import (  # noqa
    v_balanced,
    v_pain_heavy,
    v_semantic_only,
)
from . import v_i3_llm_semantic  # noqa
from . import v4_neutral_data  # noqa
