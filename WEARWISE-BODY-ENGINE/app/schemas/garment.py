"""
WearWise Garment Transport Schemas
Rejects client-supplied merchant brand_id.
"""

from datetime import datetime
from typing import List, Dict, Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class FabricPropertiesSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fibre_composition: Dict[str, float]
    mechanical_stretch_pct: float = Field(..., ge=0.0)
    stretch_recovery_pct: float = Field(..., ge=0.0, le=1.0)
    stretch_direction: Literal["rigid_zero", "mono_weft", "mono_warp", "bi_directional_four_way"]


class GarmentMeasurementItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension_code: str
    value_cm: float = Field(..., gt=0.0)
    tolerance_cm: float = Field(1.00, ge=0.0)
    measurement_procedure: str = "straight_across_relaxed"
    provenance: str = "brand_size_chart"


class GarmentSizeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    size_label: str
    sort_order: int = 0
    measurements: List[GarmentMeasurementItem] = Field(..., min_length=1)


class GarmentCreateRequest(BaseModel):
    """Merchant garment creation. brand_id is strictly forbidden (derived from merchant principal)."""
    model_config = ConfigDict(extra="forbid")

    sku: str
    title: str
    category: str
    fabric_properties: FabricPropertiesSchema


class GarmentResponse(BaseModel):
    garment_id: UUID
    brand_id: UUID
    sku: str
    title: str
    category: str
    current_revision: int
    created_at: datetime
