from __future__ import annotations

from src.models.catalog_item import Capability
from src.models.company_profile import CompanyProfile

def apply_domain_filter(
    profile: CompanyProfile,
    capabilities: list[Capability],
) -> list[Capability]:
    if not profile.active_domains:
        return []

    active = set(profile.active_domains)
    return [cap for cap in capabilities if cap.domain in active]