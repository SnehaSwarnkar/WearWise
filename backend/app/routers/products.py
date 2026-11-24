"""
GET /api/products           — list all products (with optional category & sort_price filters)
GET /api/products/{id}      — single product detail
"""

from fastapi import APIRouter, Query
from app.schemas.products import Product

router = APIRouter(prefix="/api/products", tags=["Products"])

# Static product catalogue — mirrors Explore.jsx
PRODUCTS: list[dict] = [
    {
        "id": 1,
        "name": "Cherry Baby Tee",
        "category": "Tops",
        "price": 799,
        "match": "94% Style Match",
        "className": "product-pink",
        "colors": ["#ff3d9a", "#ffffff", "#1d1d1d"],
        "brand": "WEARWISE EDIT",
        "description": "A bold, playful baby tee in cherry pink. Perfect for statement-making casual days.",
    },
    {
        "id": 2,
        "name": "Cloud Oversized Shirt",
        "category": "Tops",
        "price": 1199,
        "match": "89% Style Match",
        "className": "product-lime",
        "colors": ["#d8ff3f", "#ffffff", "#8d6bff"],
        "brand": "WEARWISE EDIT",
        "description": "A relaxed oversized shirt in citrusy lime. Easy to wear, hard to ignore.",
    },
    {
        "id": 3,
        "name": "Classic Wide Leg Denim",
        "category": "Jeans",
        "price": 1499,
        "match": "96% Style Match",
        "className": "product-blue",
        "colors": ["#6f8fe8", "#232323", "#b9d3ff"],
        "brand": "WEARWISE EDIT",
        "description": "Wide-leg silhouette in classic blue denim. The kind you wear with everything.",
    },
    {
        "id": 4,
        "name": "Sunset Mini Dress",
        "category": "Dresses",
        "price": 1899,
        "match": "92% Style Match",
        "className": "product-orange",
        "colors": ["#ff633d", "#ff3d9a", "#ffd43b"],
        "brand": "WEARWISE EDIT",
        "description": "A vibrant mini dress blending sunset orange, pink and yellow. Made for golden hours.",
    },
    {
        "id": 5,
        "name": "Electric Purple Jacket",
        "category": "Jackets",
        "price": 2299,
        "match": "91% Style Match",
        "className": "product-purple",
        "colors": ["#8d6bff", "#1d1d1d", "#ff3d9a"],
        "brand": "WEARWISE EDIT",
        "description": "A striking electric purple jacket that makes any outfit an event.",
    },
    {
        "id": 6,
        "name": "Matcha Everyday Top",
        "category": "Tops",
        "price": 899,
        "match": "88% Style Match",
        "className": "product-green",
        "colors": ["#9ecb72", "#ffffff", "#1d1d1d"],
        "brand": "WEARWISE EDIT",
        "description": "A muted matcha green top for days when you want effortless and easy.",
    },
]


@router.get("/", response_model=list[Product])
def list_products(
    category: str | None = Query(None, description="Filter by category"),
    sort_price: bool = Query(False, description="Sort ascending by price"),
):
    """Return all products, optionally filtered by category and sorted by price."""
    result = PRODUCTS[:]
    if category and category != "All":
        result = [p for p in result if p["category"] == category]
    if sort_price:
        result = sorted(result, key=lambda p: p["price"])
    return result


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: int):
    from fastapi import HTTPException
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
