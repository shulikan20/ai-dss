from __future__ import annotations
from typing import Any
from src.ingestion.normalizers.base import BaseNormalizer

class InventoryNormalizer(BaseNormalizer):
    @property
    def platform_name(self) -> str:
        return "inventory_normalizer"

    def normalize(self, raw: dict) -> dict[str, Any]:
        raise NotImplementedError("InventoryNormalizer does not work in this version.")