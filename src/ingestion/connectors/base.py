from __future__ import annotations
from abc import ABC, abstractmethod

class DataConnector(ABC):
    @abstractmethod
    def fetch(self, company_id: str) -> dict:
        """Return raw platform data as a dict."""

    @abstractmethod
    def available(self) -> bool:
        """Return True if this connector is configured and accessible."""