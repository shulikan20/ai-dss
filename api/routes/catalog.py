from __future__ import annotations
from fastapi import APIRouter, Query, Request

from api.models import CatalogCapabilityModel, CatalogResponse, ProductDetail

router = APIRouter()

def _to_product_detail(p) -> ProductDetail:
    return ProductDetail(
        product_id=getattr(p, "product_id", ""),
        name=getattr(p, "name", ""),
        vendor=getattr(p, "vendor", ""),
        url=getattr(p, "url", ""),
        cost_tier=getattr(p, "cost_tier", "unknown"),
        has_free_tier=getattr(p, "has_free_tier", False),
        gdpr_compliant=getattr(p, "gdpr_compliant", True),
        implementation_effort=getattr(p, "implementation_effort", "medium"),
        cost_notes=getattr(p, "cost_notes", ""),
        price_tier=getattr(p, "price_tier", None),
        platform_integrations=getattr(p, "platform_integrations", None),
        company_size_fit=getattr(p, "company_size_fit", None),
        setup_complexity=getattr(p, "setup_complexity", None),
    )


@router.get(
    "/catalog",
    response_model=CatalogResponse,
    summary="List all AI tool capabilities in the catalog",
)
def get_catalog(
    request: Request,
    browse_category: str | None = Query(
        default=None,
        max_length=50,
        description="Filter by library browse category (e.g. sales_crm)",
    ),
) -> CatalogResponse:
    repo = request.app.state.repo
    caps = repo.get_capabilities()

    if browse_category is not None:
        caps = [c for c in caps if getattr(c, "browse_category", None) == browse_category]
    products_by_cap: dict[str, list] = {}
    if hasattr(repo, "get_all_products"):
        for p in repo.get_all_products():
            products_by_cap.setdefault(p.capability_id, []).append(p)
    else:
        for c in caps:
            products_by_cap[c.capability_id] = repo.get_products(c.capability_id)

    return CatalogResponse(
        capabilities=[
            CatalogCapabilityModel(
                capability_id=c.capability_id,
                name=c.name,
                domain=c.domain,
                description=getattr(c, "description", ""),
                primary_outcome=getattr(c, "primary_outcome", ""),
                browse_category=getattr(c, "browse_category", None),
                products=[
                    _to_product_detail(p)
                    for p in products_by_cap.get(c.capability_id, [])
                ],
            )
            for c in caps
        ],
        total=len(caps),
    )
