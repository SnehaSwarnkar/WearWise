"""
WearWise Garment Repository
Handles catalog persistence for merchant garment profiles, specifications, sizes, and dimensions.
"""

import uuid
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    GarmentProfileModel,
    GarmentRevisionModel,
    GarmentSizeModel,
    GarmentMeasurementModel,
)


class GarmentRepository:
    """Repository for merchant garment catalog and physical size specifications."""

    def __init__(self, db: Session):
        self.db = db

    def create_garment(
        self,
        brand_id: uuid.UUID,
        sku: str,
        title: str,
        category: str,
        fabric_properties: Dict[str, Any],
    ) -> GarmentProfileModel:
        """
        Creates garment profile with initial revision 1 and fabric properties.
        """
        garment = GarmentProfileModel(
            brand_id=brand_id,
            sku=sku,
            title=title,
            category=category,
            current_revision=1,
            is_deleted=False,
        )
        self.db.add(garment)
        self.db.flush()

        rev = GarmentRevisionModel(
            garment_id=garment.id,
            revision_number=1,
            fabric_properties_json=fabric_properties,
        )
        self.db.add(rev)
        self.db.flush()
        return garment

    def get_garment(self, garment_id: uuid.UUID) -> Optional[GarmentProfileModel]:
        """Retrieves garment profile with revisions, sizes, and measurements."""
        stmt = (
            select(GarmentProfileModel)
            .where(and_(GarmentProfileModel.id == garment_id, GarmentProfileModel.is_deleted == False))  # noqa: E712
            .options(
                joinedload(GarmentProfileModel.revisions)
                .joinedload(GarmentRevisionModel.sizes)
                .joinedload(GarmentSizeModel.measurements)
            )
        )
        return self.db.scalars(stmt).unique().first()

    def get_garment_by_sku(self, brand_id: uuid.UUID, sku: str) -> Optional[GarmentProfileModel]:
        """Retrieves garment by brand_id and unique SKU."""
        stmt = (
            select(GarmentProfileModel)
            .where(
                and_(
                    GarmentProfileModel.brand_id == brand_id,
                    GarmentProfileModel.sku == sku,
                    GarmentProfileModel.is_deleted == False,  # noqa: E712
                )
            )
            .options(
                joinedload(GarmentProfileModel.revisions)
                .joinedload(GarmentRevisionModel.sizes)
                .joinedload(GarmentSizeModel.measurements)
            )
        )
        return self.db.scalars(stmt).unique().first()

    def get_latest_revision(self, garment_id: uuid.UUID) -> Optional[GarmentRevisionModel]:
        """Returns the current active garment revision with sizes and measurements."""
        stmt = (
            select(GarmentRevisionModel)
            .join(GarmentProfileModel, GarmentProfileModel.id == GarmentRevisionModel.garment_id)
            .where(
                and_(
                    GarmentRevisionModel.garment_id == garment_id,
                    GarmentRevisionModel.revision_number == GarmentProfileModel.current_revision,
                )
            )
            .options(
                joinedload(GarmentRevisionModel.sizes)
                .joinedload(GarmentSizeModel.measurements)
            )
        )
        return self.db.scalars(stmt).unique().first()

    def add_size_specification(
        self,
        garment_id: uuid.UUID,
        size_label: str,
        sort_order: int,
        measurements: List[Dict[str, Any]],
    ) -> GarmentSizeModel:
        """
        Adds or replaces a size variant specification with dimension measurements on the current revision.
        """
        rev = self.get_latest_revision(garment_id)
        if not rev:
            raise ValueError(f"Garment {garment_id} has no active revision.")

        # Check if size already exists on this revision
        existing_size = next((s for s in rev.sizes if s.size_label == size_label), None)
        if existing_size:
            size_model = existing_size
            size_model.sort_order = sort_order
            # Clear old measurements for this size
            for m in list(size_model.measurements):
                self.db.delete(m)
            self.db.flush()
        else:
            size_model = GarmentSizeModel(
                garment_revision_id=rev.id,
                size_label=size_label,
                sort_order=sort_order,
            )
            self.db.add(size_model)
            self.db.flush()

        for m in measurements:
            meas_model = GarmentMeasurementModel(
                size_id=size_model.id,
                dimension_code=m["dimension_code"],
                value_cm=Decimal(str(m["value_cm"])),
                tolerance_cm=Decimal(str(m.get("tolerance_cm", 1.00))),
                measurement_procedure=m.get("measurement_procedure", "straight_across_relaxed"),
                provenance=m.get("provenance", "brand_size_chart"),
            )
            self.db.add(meas_model)

        self.db.flush()
        return size_model
