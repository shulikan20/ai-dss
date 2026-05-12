from __future__ import annotations
from typing import Any
from src.ingestion.normalizers.base import BaseNormalizer

class CRMNormalizer(BaseNormalizer):
    @property
    def platform_name(self) -> str:
        return "crm_normalizer"

    def normalize(self, raw: dict) -> dict[str, Any]:
        raise NotImplementedError("CRMNormalizer does not work in this version.")