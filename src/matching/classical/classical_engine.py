from __future__ import annotations

import numpy as np

from src.catalog.embedder import CatalogEmbedder
from src.catalog.repository import CatalogRepository
from src.matching.base import BaseMatchEngine
from src.matching.classical.bi_encoder import BiEncoderRetriever
from src.matching.classical.cross_encoder import CrossEncoderReranker
from src.matching.classical.explanation_generator import ExplanationGenerator
from src.matching.classical.topsis_ranker import TOPSISRanker
from src.matching.filters.domain_filter import apply_domain_filter
from src.matching.filters.feasibility_filter import apply_feasibility_filter
from src.models.company_profile import CompanyProfile
from src.models.recommendation import ClassicalResult

class ClassicalEngine(BaseMatchEngine):
    def __init__(
        self,
        repo: CatalogRepository,
        embedder: CatalogEmbedder,
        retriever: BiEncoderRetriever,
        reranker: CrossEncoderReranker,
        ranker: TOPSISRanker,
        explainer: ExplanationGenerator,
        top_k: int | None = None,
    ):
        self._repo = repo
        self._embedder = embedder
        self._retriever = retriever
        self._reranker = reranker
        self._ranker = ranker
        self._explainer = explainer
        self._top_k = top_k
        self._embeddings: np.ndarray | None = None
        self._emb_index: dict[int, str] | None = None

    def name(self) -> str:
        return "classical"

    @classmethod
    def build(cls, repo: CatalogRepository, top_k: int | None = None) -> ClassicalEngine:
        return cls(
            repo=repo,
            embedder=CatalogEmbedder(repository=repo),
            retriever=BiEncoderRetriever(),
            reranker=CrossEncoderReranker(),
            ranker=TOPSISRanker(),
            explainer=ExplanationGenerator(),
            top_k=top_k,
        )

    def _get_embeddings(self) -> tuple[np.ndarray, dict[int, str]]:
        if self._embeddings is None or self._emb_index is None:
            self._embeddings, self._emb_index = self._embedder.load_embeddings()
        return self._embeddings, self._emb_index

    def _bi_scores_per_process(
        self,
        bottleneck_description: str,
        scoped_ids: set[str],
        embeddings: np.ndarray,
        index: dict[int, str],
    ) -> dict[str, float]:
        process_texts = [t.strip() for t in bottleneck_description.split(" | ") if t.strip()]
        if not process_texts:
            process_texts = [bottleneck_description]

        cap_scores: dict[str, float] = {}
        for text in process_texts:
            q_emb = self._retriever.encode_query(text)
            scores = self._retriever.retrieve(
                query_emb=q_emb,
                candidate_ids=scoped_ids,
                embeddings=embeddings,
                index=index,
                top_k=len(scoped_ids),
            )
            for cap_id, score in scores:
                cap_scores[cap_id] = max(cap_scores.get(cap_id, 0.0), score)

        return cap_scores

    def match(self, profile: CompanyProfile) -> list[ClassicalResult]:
        all_caps = self._repo.get_capabilities()
        passed, impl_map = apply_feasibility_filter(profile, all_caps, self._repo)
        scoped = apply_domain_filter(profile, passed)

        if not scoped:
            return []

        if not profile.bottleneck_description:
            bi_scores_map = {cap.capability_id: 0.5 for cap in scoped}
        else:
            embeddings, emb_index = self._get_embeddings()
            scoped_ids = {cap.capability_id for cap in scoped}
            bi_scores_map = self._bi_scores_per_process(
                profile.bottleneck_description,
                scoped_ids,
                embeddings,
                emb_index,
            )

        if not bi_scores_map:
            return []

        cap_map = {cap.capability_id: cap for cap in scoped}
        caps_ordered_by_bi = [
            cap_map[cid]
            for cid, _ in sorted(bi_scores_map.items(), key=lambda x: -x[1])
            if cid in cap_map
        ]
        reranked = self._reranker.rerank(
            query_text=profile.bottleneck_description,
            candidates=caps_ordered_by_bi,
        )
        candidates_for_topsis = [
            (cap, bi_scores_map.get(cap.capability_id, 0.0))
            for cap, _ce_score in reranked
        ]
        ranked_candidates = self._ranker.rank(
            candidates=candidates_for_topsis,
            profile=profile,
            impl_complexity_map=impl_map,
        )

        return [
            self._explainer.generate(
                candidate=candidate,
                profile=profile,
                rank=rank,
                impl_complexity_map=impl_map,
            )
            for rank, candidate in enumerate(ranked_candidates, start=1)
        ]