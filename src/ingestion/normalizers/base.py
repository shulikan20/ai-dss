from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

class BaseNormalizer(ABC):
    @abstractmethod
    def normalize(self, raw: dict) -> dict[str, Any]:
        """Compute E-tagged fields from raw export data."""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """ "shopify", "keycrm", "woocommerce", etc."""