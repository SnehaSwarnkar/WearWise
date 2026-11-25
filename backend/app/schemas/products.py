from pydantic import BaseModel, Field
from typing import Any, Optional


class Product(BaseModel):
    id: int
    name: str
    category: str
    price: int
    match: str
    className: str
    colors: list[str]
    image: Optional[str] = None
    brand: Optional[str] = "WEARWISE EDIT"
    seller_name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    published_revision: Optional[int] = None
    published_version: Optional[str] = None
    available_sizes: Optional[list[str]] = None
    size_variants: Optional[dict[str, Any]] = None
    measurement_chart: Optional[dict[str, Any]] = None
    material_profile: Optional[dict[str, Any]] = None
    storefront_images: Optional[list[dict[str, Any]]] = None
    qa_summary: Optional[dict[str, Any]] = None
    try_on_mode: Optional[str] = "IMAGE_ONLY"
    tryOnCapabilities: Optional[dict[str, Any]] = None
    rating_average: Optional[float] = None
    review_count: int = 0


class ReviewCreateRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=3, max_length=1500)
    author_name: Optional[str] = Field(None, max_length=80)
    size_purchased: Optional[str] = Field(None, max_length=16)
    fit_feedback: Optional[str] = Field(None, max_length=32)
