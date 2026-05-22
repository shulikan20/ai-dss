from __future__ import annotations
from fastapi import APIRouter, Request

from api.models import CatalogCapabilityModel, CatalogResponse

router = APIRouter()

@router.get(
    "/catalog",
    response_model=CatalogResponse,
    summary="List all AI tool capabilities in the catalog",
)
def get_catalog(request: Request) -> CatalogResponse:
    caps = request.app.state.repo.get_capabilities()

    return CatalogResponse(
        capabilities=[
            CatalogCapabilityModel(
                capability_id=c.capability_id,
                name=c.name,
                domain=c.domain,
                description=getattr(c, "description", ""),
                primary_outcome=getattr(c, "primary_outcome", ""),
            )
            for c in caps
        ],
        total=len(caps),
    )