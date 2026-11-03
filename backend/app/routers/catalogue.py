"""
Catalogue router
================
Gender-specific product catalogue with occasion and category filtering.

GET /api/catalogue/{gender}
    ?category=   western | traditional | indo-western | occasion
    ?occasion=   casual | work | festive | wedding | party
    ?sort_price= true

Gender values: men | women | boys | girls
"""

from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/api/catalogue", tags=["Catalogue"])

# ── Static catalogue ──────────────────────────────────────────────────────────
# In production replace with a database query.

_MEN = [
    # --- WESTERN ---
    {"id": 101, "name": "Classic Oxford Shirt", "gender": "men", "category": "western",
     "occasion": "work", "price": 1499, "match": "95% Style Match",
     "className": "product-blue", "colors": ["#1d4ed8", "#ffffff", "#1d1d1d"],
     "brand": "WEARWISE MEN", "description": "A timeless Oxford shirt — crisp, tailored and versatile."},
    {"id": 102, "name": "Slim Chinos", "gender": "men", "category": "western",
     "occasion": "casual", "price": 1799, "match": "91% Style Match",
     "className": "product-lime", "colors": ["#c8a96e", "#d8ff3f", "#1d1d1d"],
     "brand": "WEARWISE MEN", "description": "Relaxed slim chinos that go from desk to dinner."},
    {"id": 103, "name": "Graphic Drop Tee", "gender": "men", "category": "western",
     "occasion": "casual", "price": 899, "match": "88% Style Match",
     "className": "product-pink", "colors": ["#ff3d9a", "#ffffff", "#1d1d1d"],
     "brand": "WEARWISE MEN", "description": "A bold graphic tee for everyday self-expression."},
    {"id": 104, "name": "Tailored Blazer", "gender": "men", "category": "western",
     "occasion": "work", "price": 3499, "match": "97% Style Match",
     "className": "product-purple", "colors": ["#8d6bff", "#1d1d1d", "#ffffff"],
     "brand": "WEARWISE MEN", "description": "A sharp tailored blazer that commands the room."},
    # --- TRADITIONAL ---
    {"id": 105, "name": "Embroidered Kurta", "gender": "men", "category": "traditional",
     "occasion": "festive", "price": 1999, "match": "93% Style Match",
     "className": "product-orange", "colors": ["#ff633d", "#ffd43b", "#1d1d1d"],
     "brand": "WEARWISE MEN", "description": "A richly embroidered kurta for festive gatherings."},
    {"id": 106, "name": "Nehru Jacket", "gender": "men", "category": "traditional",
     "occasion": "wedding", "price": 2799, "match": "90% Style Match",
     "className": "product-green", "colors": ["#9ecb72", "#1d1d1d", "#ffd43b"],
     "brand": "WEARWISE MEN", "description": "A classic Nehru jacket — understated elegance."},
    {"id": 107, "name": "Sherwani Set", "gender": "men", "category": "traditional",
     "occasion": "wedding", "price": 8999, "match": "98% Style Match",
     "className": "product-purple", "colors": ["#8d6bff", "#ffd43b", "#1d1d1d"],
     "brand": "WEARWISE MEN", "description": "A grand sherwani set for your most special moments."},
    # --- INDO-WESTERN ---
    {"id": 108, "name": "Kurta with Joggers", "gender": "men", "category": "indo-western",
     "occasion": "casual", "price": 2199, "match": "89% Style Match",
     "className": "product-blue", "colors": ["#6f8fe8", "#1d1d1d", "#ffffff"],
     "brand": "WEARWISE MEN", "description": "The best of both worlds — kurta top with modern joggers."},
    {"id": 109, "name": "Bandhgala Suit", "gender": "men", "category": "indo-western",
     "occasion": "party", "price": 5999, "match": "94% Style Match",
     "className": "product-pink", "colors": ["#ff3d9a", "#1d1d1d", "#ffffff"],
     "brand": "WEARWISE MEN", "description": "A contemporary bandhgala suit that blends tradition with modernity."},
    # --- OCCASION ---
    {"id": 110, "name": "Tuxedo Set", "gender": "men", "category": "occasion",
     "occasion": "wedding", "price": 9999, "match": "99% Style Match",
     "className": "product-purple", "colors": ["#1d1d1d", "#ffffff", "#8d6bff"],
     "brand": "WEARWISE MEN", "description": "A full tuxedo for your black-tie moments."},
    {"id": 111, "name": "Party Sequin Jacket", "gender": "men", "category": "occasion",
     "occasion": "party", "price": 3999, "match": "92% Style Match",
     "className": "product-lime", "colors": ["#d8ff3f", "#1d1d1d", "#8d6bff"],
     "brand": "WEARWISE MEN", "description": "Stand out at every party in this statement sequin jacket."},
]

_WOMEN = [
    # --- WESTERN ---
    {"id": 201, "name": "Power Blazer Dress", "gender": "women", "category": "western",
     "occasion": "work", "price": 3299, "match": "96% Style Match",
     "className": "product-purple", "colors": ["#8d6bff", "#1d1d1d", "#ffffff"],
     "brand": "WEARWISE WOMEN", "description": "A sharp blazer dress that means business."},
    {"id": 202, "name": "Sunset Mini Dress", "gender": "women", "category": "western",
     "occasion": "party", "price": 1899, "match": "92% Style Match",
     "className": "product-orange", "colors": ["#ff633d", "#ff3d9a", "#ffd43b"],
     "brand": "WEARWISE WOMEN", "description": "A vibrant mini dress for golden-hour vibes."},
    {"id": 203, "name": "Wide Leg Denim", "gender": "women", "category": "western",
     "occasion": "casual", "price": 1499, "match": "94% Style Match",
     "className": "product-blue", "colors": ["#6f8fe8", "#1d1d1d", "#b9d3ff"],
     "brand": "WEARWISE WOMEN", "description": "Wide-leg silhouette denim — effortlessly cool."},
    {"id": 204, "name": "Cherry Baby Tee", "gender": "women", "category": "western",
     "occasion": "casual", "price": 799, "match": "90% Style Match",
     "className": "product-pink", "colors": ["#ff3d9a", "#ffffff", "#1d1d1d"],
     "brand": "WEARWISE WOMEN", "description": "Bold, playful and easy to style."},
    # --- TRADITIONAL ---
    {"id": 205, "name": "Embroidered Anarkali", "gender": "women", "category": "traditional",
     "occasion": "festive", "price": 4999, "match": "97% Style Match",
     "className": "product-orange", "colors": ["#ff633d", "#ffd43b", "#8d6bff"],
     "brand": "WEARWISE WOMEN", "description": "A flowing Anarkali with rich embroidery."},
    {"id": 206, "name": "Silk Saree", "gender": "women", "category": "traditional",
     "occasion": "wedding", "price": 7999, "match": "98% Style Match",
     "className": "product-purple", "colors": ["#8d6bff", "#ffd43b", "#ff633d"],
     "brand": "WEARWISE WOMEN", "description": "Timeless silk saree draped in heritage."},
    {"id": 207, "name": "Bandhani Dupatta Set", "gender": "women", "category": "traditional",
     "occasion": "festive", "price": 2499, "match": "91% Style Match",
     "className": "product-pink", "colors": ["#ff3d9a", "#ffd43b", "#ffffff"],
     "brand": "WEARWISE WOMEN", "description": "Vibrant Bandhani print — perfect for festivities."},
    # --- INDO-WESTERN ---
    {"id": 208, "name": "Dhoti Palazzo Set", "gender": "women", "category": "indo-western",
     "occasion": "party", "price": 2999, "match": "93% Style Match",
     "className": "product-lime", "colors": ["#d8ff3f", "#1d1d1d", "#ff633d"],
     "brand": "WEARWISE WOMEN", "description": "A fluid dhoti palazzo for effortless elegance."},
    {"id": 209, "name": "Jacket Kurta Set", "gender": "women", "category": "indo-western",
     "occasion": "work", "price": 3499, "match": "95% Style Match",
     "className": "product-blue", "colors": ["#1d4ed8", "#ffffff", "#ffd43b"],
     "brand": "WEARWISE WOMEN", "description": "A contemporary jacket kurta that bridges cultures."},
    # --- OCCASION ---
    {"id": 210, "name": "Lehenga Choli", "gender": "women", "category": "occasion",
     "occasion": "wedding", "price": 12999, "match": "99% Style Match",
     "className": "product-orange", "colors": ["#ff633d", "#ffd43b", "#8d6bff"],
     "brand": "WEARWISE WOMEN", "description": "A showstopping lehenga choli for your biggest day."},
    {"id": 211, "name": "Gown with Cape", "gender": "women", "category": "occasion",
     "occasion": "party", "price": 5999, "match": "96% Style Match",
     "className": "product-purple", "colors": ["#8d6bff", "#1d1d1d", "#ffffff"],
     "brand": "WEARWISE WOMEN", "description": "Dramatic and beautiful — a statement gown with a flowing cape."},
]

_BOYS = [
    {"id": 301, "name": "Cool Graphic Tee", "gender": "boys", "category": "western",
     "occasion": "casual", "price": 499, "match": "94% Style Match",
     "className": "product-blue", "colors": ["#6f8fe8", "#ffffff", "#1d1d1d"],
     "brand": "WEARWISE KIDS", "description": "Bold graphic tee for cool little guys.", "ageGroup": "6-10"},
    {"id": 302, "name": "Jogger Set", "gender": "boys", "category": "western",
     "occasion": "casual", "price": 799, "match": "92% Style Match",
     "className": "product-lime", "colors": ["#d8ff3f", "#1d1d1d", "#ffffff"],
     "brand": "WEARWISE KIDS", "description": "Comfy jogger set for active days.", "ageGroup": "6-10"},
    {"id": 303, "name": "Kurta Pajama Set", "gender": "boys", "category": "traditional",
     "occasion": "festive", "price": 1299, "match": "97% Style Match",
     "className": "product-orange", "colors": ["#ff633d", "#ffd43b", "#1d1d1d"],
     "brand": "WEARWISE KIDS", "description": "Festive kurta pajama for little celebrations.", "ageGroup": "6-10"},
    {"id": 304, "name": "Mini Sherwani", "gender": "boys", "category": "occasion",
     "occasion": "wedding", "price": 2499, "match": "99% Style Match",
     "className": "product-purple", "colors": ["#8d6bff", "#ffd43b", "#1d1d1d"],
     "brand": "WEARWISE KIDS", "description": "A tiny sherwani for the cutest little guest.", "ageGroup": "2-5"},
    {"id": 305, "name": "Denim Jacket + Tee", "gender": "boys", "category": "western",
     "occasion": "casual", "price": 1099, "match": "90% Style Match",
     "className": "product-blue", "colors": ["#6f8fe8", "#1d1d1d", "#ffffff"],
     "brand": "WEARWISE KIDS", "description": "Mini denim jacket with a matching tee.", "ageGroup": "11-14"},
    {"id": 306, "name": "Indo-Western Jacket Set", "gender": "boys", "category": "indo-western",
     "occasion": "party", "price": 1799, "match": "91% Style Match",
     "className": "product-pink", "colors": ["#ff3d9a", "#1d1d1d", "#ffd43b"],
     "brand": "WEARWISE KIDS", "description": "A festive indo-western jacket set for parties.", "ageGroup": "11-14"},
]

_GIRLS = [
    {"id": 401, "name": "Floral Dress", "gender": "girls", "category": "western",
     "occasion": "casual", "price": 699, "match": "95% Style Match",
     "className": "product-pink", "colors": ["#ff3d9a", "#ffffff", "#ffd43b"],
     "brand": "WEARWISE KIDS", "description": "A sweet floral dress for everyday wear.", "ageGroup": "2-5"},
    {"id": 402, "name": "Lehenga for Girls", "gender": "girls", "category": "traditional",
     "occasion": "festive", "price": 1999, "match": "98% Style Match",
     "className": "product-orange", "colors": ["#ff633d", "#ffd43b", "#8d6bff"],
     "brand": "WEARWISE KIDS", "description": "A beautiful little lehenga for festive occasions.", "ageGroup": "6-10"},
    {"id": 403, "name": "Crop Top + Skirt Set", "gender": "girls", "category": "western",
     "occasion": "party", "price": 999, "match": "92% Style Match",
     "className": "product-purple", "colors": ["#8d6bff", "#ff3d9a", "#ffffff"],
     "brand": "WEARWISE KIDS", "description": "Fun and age-appropriate party set.", "ageGroup": "11-14"},
    {"id": 404, "name": "Anarkali Suit", "gender": "girls", "category": "occasion",
     "occasion": "wedding", "price": 2999, "match": "97% Style Match",
     "className": "product-orange", "colors": ["#ff633d", "#8d6bff", "#ffd43b"],
     "brand": "WEARWISE KIDS", "description": "A gorgeous anarkali suit for wedding functions.", "ageGroup": "6-10"},
    {"id": 405, "name": "Dungaree Set", "gender": "girls", "category": "western",
     "occasion": "casual", "price": 849, "match": "89% Style Match",
     "className": "product-lime", "colors": ["#d8ff3f", "#1d1d1d", "#ff3d9a"],
     "brand": "WEARWISE KIDS", "description": "Playful dungaree set for little adventurers.", "ageGroup": "2-5"},
    {"id": 406, "name": "Indo-Western Gown", "gender": "girls", "category": "indo-western",
     "occasion": "party", "price": 1499, "match": "93% Style Match",
     "className": "product-pink", "colors": ["#ff3d9a", "#ffd43b", "#8d6bff"],
     "brand": "WEARWISE KIDS", "description": "A chic indo-western gown for celebrations.", "ageGroup": "11-14"},
]

_ALL = _MEN + _WOMEN + _BOYS + _GIRLS


@router.get("/{gender}")
def get_catalogue(
    gender: str,
    category: Optional[str] = Query(None),
    occasion: Optional[str] = Query(None),
    age_group: Optional[str] = Query(None),
    sort_price: bool = Query(False),
):
    """
    Return products for a gender (men | women | boys | girls).
    Optional filters: category, occasion, age_group, sort_price.
    """
    valid = {"men", "women", "boys", "girls"}
    if gender not in valid:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"gender must be one of {valid}")

    result = [p for p in _ALL if p["gender"] == gender]

    if category:
        result = [p for p in result if p["category"] == category]
    if occasion:
        result = [p for p in result if p["occasion"] == occasion]
    if age_group:
        result = [p for p in result if p.get("ageGroup") == age_group]
    if sort_price:
        result = sorted(result, key=lambda p: p["price"])

    return result
