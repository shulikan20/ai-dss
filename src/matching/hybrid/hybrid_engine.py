from __future__ import annotations
import warnings
import requests

from src.catalog.repository import CatalogRepository
from src.matching.base import BaseMatchEngine
from src.matching.classical.classical_engine import ClassicalEngine
from src.matching.hybrid.shortlist_reranker import ShortlistReranker
from src.models.company_profile import CompanyProfile
from src.models.recommendation import ClassicalResult

class HybridEngine(BaseMatchEngine):
    _DEFAULT_TOP_K: int = 8

    def __init__(
        self,
        classical_engine: ClassicalEngine,
        reranker: ShortlistReranker,
        top_k: int = _DEFAULT_TOP_K,
    ):
        self._classical = classical_engine
        self._reranker = reranker
        self._top_k = top_k

    @classmethod
    def build(
        cls,
        repo: CatalogRepository,
        top_k: int = _DEFAULT_TOP_K,
    ) -> HybridEngine:
        classical_engine = ClassicalEngine.build(repo=repo)
        reranker = ShortlistReranker(top_k=top_k)
        return cls(
            classical_engine=classical_engine,
            reranker=reranker,
            top_k=top_k,
        )
    
    def name(self) -> str:
        return "hybrid"

    def match(self, profile: CompanyProfile) -> list[ClassicalResult]:
        classical_results = self._classical.match(profile)
        if not classical_results:
            return []

        shortlist = classical_results[: self._top_k]

        try:
            reranked_ids = self._reranker.rerank(profile, shortlist)
        except requests.exceptions.ConnectionError:
            warnings.warn(
                "HybridEngine: Ollama is not running - falling back to classical ordering. "
                "Start Ollama with: ollama serve",
                RuntimeWarning,
                stacklevel=2,
            )
            return classical_results

        shortlist_map = {r.capability_id: r for r in shortlist}
        tail = [r for r in classical_results if r.capability_id not in shortlist_map]
        reordered: list[ClassicalResult] = []

        for new_rank, cap_id in enumerate(reranked_ids, start=1):
            if cap_id in shortlist_map:
                result = shortlist_map[cap_id]
                reordered.append(
                    result.__class__(
                        rank=new_rank,
                        capability_id=result.capability_id,
                        capability_name=result.capability_name,
                        domain=result.domain,
                        topsis_score=result.topsis_score,
                        dimensions=result.dimensions,
                        explanation=result.explanation,
                        impl_complexity=result.impl_complexity,
                    )
                )

        tail_start_rank = len(reordered) + 1
        for i, r in enumerate(tail):
            reordered.append(
                r.__class__(
                    rank=tail_start_rank + i,
                    capability_id=r.capability_id,
                    capability_name=r.capability_name,
                    domain=r.domain,
                    topsis_score=r.topsis_score,
                    dimensions=r.dimensions,
                    explanation=r.explanation,
                    impl_complexity=r.impl_complexity,
                )
            )

        return reordered