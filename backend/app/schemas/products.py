from pydantic import BaseModel
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
