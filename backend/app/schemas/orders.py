from pydantic import BaseModel, EmailStr
from typing import Optional


class CustomerInfo(BaseModel):
    firstName: str
    lastName: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    pincode: str


class PlaceOrderRequest(BaseModel):
    session_id: str
    customer: CustomerInfo
    paymentMethod: str  # upi | card | cod
    idempotency_key: Optional[str] = None


class OrderItem(BaseModel):
    id: int
    name: str
    price: int
    quantity: int = 1
    image: Optional[str] = None
    brand: Optional[str] = None
    size: Optional[str] = None
    sku: Optional[str] = None
    published_revision: Optional[int] = None


class OrderResponse(BaseModel):
    id: str
    items: list[OrderItem]
    customer: CustomerInfo
    paymentMethod: str
    subtotal: int
    shipping: int
    total: int
    createdAt: str
    status: str
    is_demo_checkout: bool = True
    payment_status: str = "DEMO_NO_PAYMENT_CAPTURED"
