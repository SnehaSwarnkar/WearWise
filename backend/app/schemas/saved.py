from pydantic import BaseModel
from typing import Optional


class SavedLook(BaseModel):
    id: str
    session_id: str
    name: str
    description: Optional[str] = None
    image: Optional[str] = None
    created_at: str


class WishlistItem(BaseModel):
    id: str
    session_id: str
    product_id: int
    name: str
    price: int
    image: Optional[str] = None
    brand: Optional[str] = None
    created_at: str


class SaveLookRequest(BaseModel):
    session_id: str
    name: str
    description: Optional[str] = None
    image: Optional[str] = None


class SaveWishlistRequest(BaseModel):
    session_id: str
    product_id: int
    name: str
    price: int
    image: Optional[str] = None
    brand: Optional[str] = None
