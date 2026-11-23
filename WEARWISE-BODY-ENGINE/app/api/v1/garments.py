"""
FastAPI Router for Merchant Garment Management
Endpoint base: /api/v1/garments
"""

import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.auth import get_current_brand_id
from app.services.garment_service import GarmentService
from app.api.schemas.garment import (
    CreateGarmentRequest,
    AddGarmentSizeRequest,
    GarmentResponse,
    GarmentSizeResponse,
)

router = APIRouter(prefix="/garments", tags=["Merchant Garment Catalog"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=GarmentResponse)
def create_garment(
    payload: CreateGarmentRequest,
    brand_id: uuid.UUID = Depends(get_current_brand_id),
    db: Session = Depends(get_db),
):
    """
    Creates a new garment profile and initial revision for the authenticated brand.
    """
    srv = GarmentService(db)
    garment = srv.create_garment(
        requesting_brand_id=brand_id,
        sku=payload.sku,
        title=payload.title,
        category=payload.category,
        fabric_properties=payload.fabric_properties,
    )
    db.commit()

    latest_rev = srv.repo.get_latest_revision(garment.id)
    return GarmentResponse(
        garment_id=str(garment.id),
        brand_id=str(garment.brand_id),
        sku=garment.sku,
        title=garment.title,
        category=garment.category,
        current_revision=garment.current_revision,
        fabric_properties=latest_rev.fabric_properties_json if latest_rev else {},
        sizes=[],
        created_at=garment.created_at.isoformat(),
    )


@router.post("/{garment_id}/sizes", status_code=status.HTTP_201_CREATED)
def add_garment_size(
    garment_id: uuid.UUID,
    payload: AddGarmentSizeRequest,
    brand_id: uuid.UUID = Depends(get_current_brand_id),
    db: Session = Depends(get_db),
):
    """
    Adds or updates a size specification on the active garment revision.
    """
    srv = GarmentService(db)
    meas_dicts = [m.model_dump() for m in payload.measurements]
    size_model = srv.add_size_specification(
        garment_id=garment_id,
        requesting_brand_id=brand_id,
        size_label=payload.size_label,
        sort_order=payload.sort_order,
        measurements=meas_dicts,
    )
    db.commit()

    return {
        "garment_id": str(garment_id),
        "size_id": str(size_model.id),
        "size_label": size_model.size_label,
        "dimension_count": len(payload.measurements),
    }


@router.get("/{garment_id}", response_model=GarmentResponse)
def get_garment(
    garment_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieves garment specification and complete size table."""
    srv = GarmentService(db)
    garment = srv.get_garment(garment_id)
    latest_rev = srv.repo.get_latest_revision(garment_id)

    sizes_resp = []
    if latest_rev:
        for s in latest_rev.sizes:
            sizes_resp.append(
                GarmentSizeResponse(
                    size_label=s.size_label,
                    sort_order=s.sort_order,
                    measurements={m.dimension_code: float(m.value_cm) for m in s.measurements},
                )
            )

    return GarmentResponse(
        garment_id=str(garment.id),
        brand_id=str(garment.brand_id),
        sku=garment.sku,
        title=garment.title,
        category=garment.category,
        current_revision=garment.current_revision,
        fabric_properties=latest_rev.fabric_properties_json if latest_rev else {},
        sizes=sizes_resp,
        created_at=garment.created_at.isoformat(),
    )


@router.get("/{garment_id}/revisions")
def get_garment_revisions(
    garment_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieves specification revisions for a garment."""
    srv = GarmentService(db)
    garment = srv.get_garment(garment_id)
    return {
        "garment_id": str(garment_id),
        "revisions": [
            {
                "revision_number": r.revision_number,
                "created_at": r.created_at.isoformat(),
                "size_count": len(r.sizes),
            }
            for r in garment.revisions
        ],
    }
