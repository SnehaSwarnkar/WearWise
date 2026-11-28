"""
Pydantic Schemas for Merchant Garment Management
"""

from typing import Dict, List, Any, Optional
import uuid
from pydantic import BaseModel, Field


class CreateGarmentRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=256)
    category: str = Field(..., pattern="^(t_shirt|casual_shirt|trousers|jeans)$")
    fabric_properties: Dict[str, Any]


class GarmentMeasurementItem(BaseModel):
    dimension_code: str
    value_cm: float = Field(..., gt=0.0)
    tolerance_cm: float = 1.00
    measurement_procedure: str = "straight_across_relaxed"
    provenance: str = "brand_size_chart"


class AddGarmentSizeRequest(BaseModel):
    size_label: str
    sort_order: int = 0
    measurements: List[GarmentMeasurementItem]


class GarmentSizeResponse(BaseModel):
    size_label: str
    sort_order: int
    measurements: Dict[str, float]


class GarmentResponse(BaseModel):
    garment_id: str
    brand_id: str
    sku: str
    title: str
    category: str
    current_revision: int
    fabric_properties: Dict[str, Any]
    sizes: List[GarmentSizeResponse]
    created_at: str
