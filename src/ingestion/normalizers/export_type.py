from __future__ import annotations

from enum import Enum

class ExportType(str, Enum):
    ORDERS = "orders"
    MARKETING = "marketing"
    SUPPORT = "support"
    INVENTORY = "inventory"
    CRM = "crm"
    UNSTRUCTURED = "unstructured"

    @classmethod
    def from_string(cls, value: str) -> ExportType | None:
        try:
            return cls(value.lower().strip())
        except ValueError:
            return None

class NormalizerRegistry:
    _registry: dict[ExportType, object] | None = None

    @classmethod
    def get(cls, export_type: ExportType | str):
        if cls._registry is None:
            cls._build()
        if isinstance(export_type, ExportType):
            key = export_type
        elif isinstance(export_type, str):
            key = ExportType.from_string(export_type)
        else:
            return None
        if key is None:
            return None
        return cls._registry.get(key)

    @classmethod
    def _build(cls) -> None:
        from src.ingestion.normalizers.order import OrderNormalizer
        from src.ingestion.normalizers.marketing import MarketingNormalizer
        from src.ingestion.normalizers.support_tickets import SupportTicketsNormalizer
        from src.ingestion.normalizers.inventory import InventoryNormalizer
        from src.ingestion.normalizers.crm import CRMNormalizer

        cls._registry = {
            ExportType.ORDERS: OrderNormalizer(),
            ExportType.MARKETING: MarketingNormalizer(),
            ExportType.SUPPORT: SupportTicketsNormalizer(),
            ExportType.INVENTORY: InventoryNormalizer(),
            ExportType.CRM: CRMNormalizer(),
        }