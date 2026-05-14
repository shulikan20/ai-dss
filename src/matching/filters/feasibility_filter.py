from __future__ import annotations

from typing import TYPE_CHECKING

from src.models.catalog_item import Capability, ImplComplexity
from src.models.company_profile import CompanyProfile

if TYPE_CHECKING:
    from src.catalog.repository import CatalogRepository

def apply_feasibility_filter(
    profile: CompanyProfile,
    capabilities: list[Capability],
    repo: CatalogRepository,
) -> tuple[list[Capability], dict[str, ImplComplexity]]:
    gdpr_capable_ids: set[str] = set()
    has_products_ids: set[str] = set()
    if profile.is_eu:
        gdpr_capable_ids = repo.get_gdpr_capable_capability_ids()
        has_products_ids = repo.get_capability_ids_with_products()
    passed: list[Capability] = []
    impl_complexity_map: dict[str, ImplComplexity] = {}

    for cap in capabilities:
        if (
            profile.is_eu
            and cap.capability_id in has_products_ids
            and cap.capability_id not in gdpr_capable_ids
        ):
            continue

        gap = cap.min_technical_capability - profile.technical_level
        if gap > 0:
            if not profile.implementation_support_requested:
                continue
            impl_complexity_map[cap.capability_id] = (
                ImplComplexity.MEDIUM if gap == 1 else ImplComplexity.HIGH
            )
        elif profile.implementation_support_requested:
            impl_complexity_map[cap.capability_id] = ImplComplexity.LOW

        passed.append(cap)

    return passed, impl_complexity_map