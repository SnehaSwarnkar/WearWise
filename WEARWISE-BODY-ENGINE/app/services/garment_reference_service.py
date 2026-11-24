"""
WearWise Garment Reference Service
Resolves commercial garment product details, front reference image,
optional rear and side reference images, and marks inferred view details.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("wearwise.vton.garment_reference")


class GarmentReferenceService:
    """Resolves merchant garment assets and provides multi-view reference metadata."""

    # Curated commerce catalog lookup fallback for prototype demonstration
    CATALOG_METADATA = {
        "TSH-WW-CREW-001": {
            "sku": "TSH-WW-CREW-001",
            "title": "Signature Boxy Crew Tee / Cherry Baby Tee",
            "category": "tops",
            "brand": "WEARWISE EDIT",
            "primary_color": "#ff3d9a",
            "fabric": "100% Combed Cotton, 220 GSM",
            "front_image_url": "/garments/TSH-WW-CREW-001.glb",
            "has_side_reference": False,
            "has_back_reference": False,
            "side_inferred_note": "AI-inferred from frontal design; sleeve drape and side seam provisional.",
            "back_inferred_note": "AI-inferred from frontal design; back graphics and rear collar seam provisional.",
        },
        "TSH-WW-OVERSIZE-002": {
            "sku": "TSH-WW-OVERSIZE-002",
            "title": "Cloud Oversized Shirt",
            "category": "tops",
            "brand": "WEARWISE EDIT",
            "primary_color": "#d8ff3f",
            "fabric": "Poplin Cotton Blend",
            "front_image_url": None,
            "has_side_reference": False,
            "has_back_reference": False,
            "side_inferred_note": "AI-inferred from frontal design.",
            "back_inferred_note": "AI-inferred from frontal design.",
        },
    }

    def __init__(self, db_session=None):
        self.db = db_session

    def resolve_references(self, sku: str) -> Dict[str, Any]:
        """
        Resolves product imagery and flags whether side and rear views are real or inferred.
        """
        meta = self.CATALOG_METADATA.get(sku)
        if not meta:
            # Generic fallback
            meta = {
                "sku": sku,
                "title": f"Garment {sku}",
                "category": "tops",
                "brand": "WEARWISE",
                "primary_color": "#151515",
                "fabric": "Standard Cotton Blend",
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
            "fabric": meta["fabric"],
            "views": {
                "front": {
                    "is_inferred": False,
                    "confidence": 0.98,
                    "description": "Frontal try-on generated with high-fidelity texture transfer.",
                },
                "side": {
                    "is_inferred": not meta["has_side_reference"],
                    "confidence": 0.85 if not meta["has_side_reference"] else 0.96,
                    "disclaimer": meta["side_inferred_note"] if not meta["has_side_reference"] else None,
                    "description": "Lateral profile view depicting side seam alignment and sleeve drape.",
                },
                "back": {
                    "is_inferred": not meta["has_back_reference"],
                    "confidence": 0.82 if not meta["has_back_reference"] else 0.95,
                    "disclaimer": meta["back_inferred_note"] if not meta["has_back_reference"] else None,
                    "description": "Dorsal rear view depicting back silhouette and neckline finish.",
                },
            },
        }
