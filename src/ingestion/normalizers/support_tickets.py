from __future__ import annotations
from typing import Any
from src.ingestion.normalizers.base import BaseNormalizer

class SupportTicketsNormalizer(BaseNormalizer):
    @property
    def platform_name(self) -> str:
        return "support_tickets_normalizer"

    def normalize(self, raw: dict) -> dict[str, Any]:
        raise NotImplementedError("SupportTicketsNormalizer does not work in this version.")