from pydantic import BaseModel
from typing import Optional


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
