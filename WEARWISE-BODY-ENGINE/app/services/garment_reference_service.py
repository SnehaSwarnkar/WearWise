"""
WearWise Garment Reference Service
Resolves commercial garment product details, front reference image,
optional rear and side reference images, and marks inferred view details.
Checks active MongoDB `catalog_publications` before static fallback metadata.
"""

import logging
from typing import Any, Dict

from app.db import mongo

logger = logging.getLogger("wearwise.vton.garment_reference")


class GarmentReferenceService:
    """Resolves merchant garment assets and provides multi-view reference metadata."""

    CATALOG_METADATA = {
        "TSH-WW-CREW-001": {
            "sku": "TSH-WW-CREW-001",
            "title": "Cherry Baby Tee",
            "category": "Tops",
            "brand": "WEARWISE EDIT",
            "primary_color": "#ff3d9a",
            "front_image_url": "/garments/reference_front.jpg",
            "has_side_reference": True,
            "has_back_reference": False,
            "side_inferred_note": None,
            "back_inferred_note": "Rear view not yet supplied by seller.",
        },
        "TSH-WW-OVERSIZE-002": {
            "sku": "TSH-WW-OVERSIZE-002",
            "title": "Cloud Oversized Shirt",
            "category": "Tops",
            "brand": "WEARWISE EDIT",
            "primary_color": "#d8ff3f",
            "front_image_url": None,
            "has_side_reference": False,
            "has_back_reference": False,
            "side_inferred_note": "Inferred when side view is unavailable.",
            "back_inferred_note": "Inferred when rear view is unavailable.",
        },
    }

    def __init__(self, db_session=None):
        self.db = db_session

    def resolve_references(self, sku: str) -> Dict[str, Any]:
        meta: Dict[str, Any] | None = None

        cp_col = mongo.get_commerce_collection("catalog_publications")
        if cp_col is not None:
            pub = cp_col.find_one({"sku": sku, "status": "published"}, {"_id": 0})
            if pub:
                imgs = pub.get("storefront_images") or []
                front_img = next((im.get("url") for im in imgs if im.get("viewpoint") == "front"), None)
                if not front_img and imgs:
                    front_img = imgs[0].get("url")
                has_side = any(im.get("viewpoint") in ("left_side", "right_side", "side") for im in imgs)
                has_back = any(im.get("viewpoint") == "back" for im in imgs)
                meta = {
                    "sku": pub.get("sku", sku),
                    "title": pub.get("name", f"Garment {sku}"),
                    "category": pub.get("category", "Tops"),
                    "brand": pub.get("brand_id", "WEARWISE"),
                    "primary_color": pub.get("color_variant", "#151515"),
                    "front_image_url": front_img,
                    "has_side_reference": has_side,
                    "has_back_reference": has_back,
                    "side_inferred_note": None if has_side else "AI-inferred from frontal design.",
                    "back_inferred_note": None if has_back else "AI-inferred from frontal design.",
                }

        if meta is None:
            meta = self.CATALOG_METADATA.get(sku)

        if not meta:
            meta = {
                "sku": sku,
                "title": f"Garment {sku}",
                "category": "Tops",
                "brand": "WEARWISE",
                "primary_color": "#151515",
                "front_image_url": None,
                "has_side_reference": False,
                "has_back_reference": False,
                "side_inferred_note": "AI-inferred from frontal design.",
                "back_inferred_note": "AI-inferred from frontal design.",
            }

        return {
            "sku": meta["sku"],
            "title": meta["title"],
            "category": meta["category"],
            "brand": meta["brand"],
            "primary_color": meta["primary_color"],
            "front_image_url": meta.get("front_image_url"),
            "views": {
                "front": {
                    "is_inferred": False,
                    "confidence": 0.98,
                    "description": "Frontal virtual try-on view.",
                },
                "side": {
                    "is_inferred": not meta["has_side_reference"],
                    "confidence": 0.85 if not meta["has_side_reference"] else 0.96,
                    "disclaimer": meta["side_inferred_note"] if not meta["has_side_reference"] else None,
                    "description": "Lateral profile view.",
                },
                "back": {
                    "is_inferred": not meta["has_back_reference"],
                    "confidence": 0.82 if not meta["has_back_reference"] else 0.95,
                    "disclaimer": meta["back_inferred_note"] if not meta["has_back_reference"] else None,
                    "description": "Rear view.",
                },
            },
        }
