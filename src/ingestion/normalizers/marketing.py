from __future__ import annotations
from typing import Any
from src.ingestion.normalizers.base import BaseNormalizer

class MarketingNormalizer(BaseNormalizer):
    @property
    def platform_name(self) -> str:
        return "marketing_normalizer"

    def normalize(self, raw: dict) -> dict[str, Any]:
        raise NotImplementedError("MarketingNormalizer does not work in this version.")