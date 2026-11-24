from pydantic import BaseModel
from typing import Optional


class CartItem(BaseModel):
    id: int
    name: str
    price: int
    quantity: int = 1
    image: Optional[str] = None
    brand: Optional[str] = "WEARWISE EDIT"
    color: Optional[str] = None
    size: Optional[str] = None
    sku: Optional[str] = None


class CartAddRequest(BaseModel):
    session_id: str
    item: CartItem


class CartUpdateRequest(BaseModel):
    session_id: str
    item_id: int
    quantity: int
    size: Optional[str] = None


class CartRemoveRequest(BaseModel):
    session_id: str
    item_id: int
    size: Optional[str] = None


class CartResponse(BaseModel):
    session_id: str
    items: list[CartItem]
    subtotal: int
    shipping: int
    total: int
