from __future__ import annotations

from typing import TYPE_CHECKING
import numpy as np
from config import CFG

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

class BiEncoderRetriever:
    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or CFG.BI_ENCODER_MODEL
        self._model: _ST | None = None  # type: ignore[name-defined]

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise ImportError(
                    "sentence-transformers is not installed. "
                    "Run: pip install sentence-transformers"
                ) from exc
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def encode_query(self, text: str) -> np.ndarray:
        model = self._get_model()
        emb: np.ndarray = model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        emb = emb.astype(np.float32)
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        return emb

    def retrieve(
        self,
        query_emb: np.ndarray,
        candidate_ids: set[str],
        embeddings: np.ndarray,
        index: dict[int, str],
        top_k: int | None = None,
    ) -> list[tuple[str, float]]:
        k = min(top_k or CFG.BI_ENCODER_TOP_K, len(candidate_ids))
        if k == 0 or not candidate_ids:
            return []
        rev_index: dict[str, int] = {cap_id: row for row, cap_id in index.items()}

        scoped: list[tuple[str, int]] = [
            (cap_id, rev_index[cap_id])
            for cap_id in candidate_ids
            if cap_id in rev_index
        ]

        if not scoped:
            return []

        rows = np.array([row for _, row in scoped], dtype=np.intp)
        sub_emb = embeddings[rows]
        scores: np.ndarray = sub_emb @ query_emb
        top_indices = np.argsort(-scores)[:k]
        return [
            (scoped[i][0], float(scores[i]))
            for i in top_indices
        ]