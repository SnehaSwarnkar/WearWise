"""
WearWise Garment Application Service
Manages garment catalog creation, fabric specifications, and size dimension specifications.
Strictly verifies merchant brand ownership.
"""

import uuid
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from app.repositories.garment_repository import GarmentRepository
from app.db.models import GarmentProfileModel, GarmentSizeModel
from app.services.errors import NotFoundError, ForbiddenError, ValidationError


class GarmentService:
    """Application service for merchant garment catalog operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = GarmentRepository(db)

    def create_garment(
        self,
        requesting_brand_id: uuid.UUID,
        sku: str,
        title: str,
        category: str,
        fabric_properties: Dict[str, Any],
    ) -> GarmentProfileModel:
        """
        Creates a new garment profile and initial revision for the authenticated merchant brand.
        """
        if not sku or not sku.strip():
            raise ValidationError("SKU must be a non-empty string.")
        if not title or not title.strip():
            raise ValidationError("Title must be a non-empty string.")
        if category not in ("t_shirt", "casual_shirt", "trousers", "jeans"):
            raise ValidationError(f"Category '{category}' is not supported in Phase 6A.")

        # Check for existing SKU under this brand
        existing = self.repo.get_garment_by_sku(requesting_brand_id, sku)
        if existing:
            raise ValidationError(f"Garment with SKU '{sku}' already exists for this brand.")

        return self.repo.create_garment(
            brand_id=requesting_brand_id,
            sku=sku,
            title=title,
            category=category,
            fabric_properties=fabric_properties,
        )

    def get_garment(self, garment_id: uuid.UUID) -> GarmentProfileModel:
        """Retrieves garment specification by id."""
        garment = self.repo.get_garment(garment_id)
        if not garment:
            raise NotFoundError(f"Garment {garment_id} not found.")
        return garment

    def list_garments(self, brand_id: Optional[uuid.UUID] = None, limit: int = 50) -> List[GarmentProfileModel]:
        """Lists available garments in the catalog."""
        return self.repo.list_garments(brand_id=brand_id, limit=limit)

    def add_size_specification(
        self,
        garment_id: uuid.UUID,
        requesting_brand_id: uuid.UUID,
        size_label: str,
        sort_order: int,
        measurements: List[Dict[str, Any]],
    ) -> GarmentSizeModel:
        """
        Adds size specification to garment after verifying brand ownership.
        """
        garment = self.get_garment(garment_id)
        if garment.brand_id != requesting_brand_id:
            raise ForbiddenError(
                "Access denied: You do not own this garment catalog record.",
                code="BRAND_OWNERSHIP_VIOLATION",
            )

        if not size_label or not size_label.strip():
            raise ValidationError("size_label must be a non-empty string.")

        return self.repo.add_size_specification(
            garment_id=garment_id,
            size_label=size_label,
            sort_order=sort_order,
            measurements=measurements,
        )
