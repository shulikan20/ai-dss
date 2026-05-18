from __future__ import annotations

from typing import TYPE_CHECKING
import numpy as np
from config import CFG
from src.models.catalog_item import Capability

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder as _CE

class CrossEncoderReranker:
    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or CFG.CROSS_ENCODER_MODEL
        self._model: _CE | None = None  # type: ignore[name-defined]

    def _get_model(self) -> _CE:
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
            except ImportError as exc:
                raise ImportError(
                    "sentence-transformers is not installed. "
                    "Run: pip install sentence-transformers"
                ) from exc
            self._model = CrossEncoder(self._model_name)
        return self._model

    def rerank(
        self,
        query_text: str,
        candidates: list[Capability],
    ) -> list[tuple[Capability, float]]:
        if not candidates:
            return []

        model = self._get_model()
        pairs = [(query_text, cap.description) for cap in candidates]
        logits: np.ndarray = np.array(model.predict(pairs), dtype=np.float32)
        scores = self._sigmoid(logits)
        ranked = sorted(
            zip(candidates, scores.tolist()),
            key=lambda x: -x[1],
        )
        return ranked
    
    @staticmethod
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        result = np.empty_like(x, dtype=np.float32)
        pos = x >= 0
        result[pos] = 1.0 / (1.0 + np.exp(-x[pos]))
        neg_exp = np.exp(x[~pos])
        result[~pos] = neg_exp / (1.0 + neg_exp)
        return result