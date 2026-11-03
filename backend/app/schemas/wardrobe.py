from pydantic import BaseModel
from typing import Optional


class WardrobeItem(BaseModel):
    id: str
    session_id: str
    name: str
    category: str  # Tops | Bottoms | Dresses | Shoes | Accessories
    image_url: str
    created_at: str


class WardrobeItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
