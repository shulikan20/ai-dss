from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from config import CFG
from src.catalog.repository import CatalogRepository
from src.models.catalog_item import Capability

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer as _ST

class CatalogEmbedder:
    INDEX_SUFFIX = "_index.json"

    def __init__(
        self,
        repository: CatalogRepository,
        embeddings_path: Path | str | None = None,
        model_name: str | None = None,
    ):
        self._repo = repository
        self._embeddings_path = (
            Path(embeddings_path) if embeddings_path else CFG.EMBEDDINGS_PATH
        )
        self._index_path = (
            self._embeddings_path.parent
            / (self._embeddings_path.stem + self.INDEX_SUFFIX)
        )
        self._model_name = model_name or CFG.BI_ENCODER_MODEL
        self._model: _ST | None = None

    def _get_model(self) -> _ST:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers is not installed. "
                    "Run: pip install sentence-transformers"
                ) from e
            self._model = SentenceTransformer(self._model_name)
        return self._model

    @staticmethod
    def build_embedding_text(cap: Capability) -> str:
        parts: list[str] = []
        if cap.description:
            parts.append(cap.description)
        if cap.bottleneck_keywords:
            parts.append(" ".join(cap.bottleneck_keywords))
        return " ".join(parts)

    def compute_embeddings(self) -> np.ndarray:
        capabilities = self._repo.get_capabilities()
        if not capabilities:
            raise ValueError(
                "No capabilities found in catalog. "
                "Run build_catalog.py to seed the database."
            )

        texts = [self.build_embedding_text(cap) for cap in capabilities]
        capability_ids = [cap.capability_id for cap in capabilities]
        print(f"Encoding {len(texts)} capabilities with {self._model_name}...")
        model = self._get_model()
        embeddings: np.ndarray = model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        self._embeddings_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(str(self._embeddings_path), embeddings)

        index = {str(i): cap_id for i, cap_id in enumerate(capability_ids)}
        with self._index_path.open("w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)

        print(
            f"Saved embeddings: {self._embeddings_path}  "
            f"shape={embeddings.shape}"
        )
        print(f"Saved index:      {self._index_path}")
        return embeddings

    def load_embeddings(self) -> tuple[np.ndarray, dict[int, str]]:
        if not self._embeddings_path.exists():
            raise FileNotFoundError(
                f"Embeddings file not found: {self._embeddings_path}\n"
                "Run: python -m src.catalog.embedder"
            )
        if not self._index_path.exists():
            raise FileNotFoundError(
                f"Embeddings index not found: {self._index_path}\n"
                "Run: python -m src.catalog.embedder"
            )

        embeddings = np.load(str(self._embeddings_path))
        with self._index_path.open(encoding="utf-8") as f:
            raw = json.load(f)

        index = {int(k): v for k, v in raw.items()}
        return embeddings, index

    def embeddings_exist(self) -> bool:
        return self._embeddings_path.exists() and self._index_path.exists()

if __name__ == "__main__":
    with CatalogRepository() as repo:
        embedder = CatalogEmbedder(repository=repo)
        embedder.compute_embeddings()