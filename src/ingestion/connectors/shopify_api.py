from __future__ import annotations

from src.ingestion.connectors.base import DataConnector

class ShopifyApiConnector(DataConnector):
    def __init__(self, shop_domain: str, access_token: str):
        self._shop = shop_domain
        self._token = access_token

    def available(self) -> bool:
        raise NotImplementedError("ShopifyApiConnector does not work in this version.")

    def fetch(self, company_id: str) -> dict:
        raise NotImplementedError("ShopifyApiConnector does not work in this version.")