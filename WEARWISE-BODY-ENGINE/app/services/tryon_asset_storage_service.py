"""
WearWise Try-On Asset Storage Service
Manages private disk storage for AI virtual try-on inputs and multi-view output assets.
Enforces content-addressable storage, strict user privacy, and complete deletion lifecycle.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional, List
from PIL import Image

logger = logging.getLogger("wearwise.vton.storage")


class TryOnAssetStorageService:
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            from app.config import DATA_DIR
            self.assets_dir = DATA_DIR / "assets" / "vton"
            self.uploads_dir = DATA_DIR / "uploads" / "vton"
        else:
            self.assets_dir = base_dir / "assets" / "vton"
            self.uploads_dir = base_dir / "uploads" / "vton"

        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def save_view_image(self, job_id: str, view_type: str, img: Image.Image) -> tuple[str, str]:
        """
        Saves a single try-on view image as an individual, distinct asset file.
        Returns: (absolute_file_path, relative_url)
        """
        filename = f"{job_id}_{view_type}.png"
        filepath = self.assets_dir / filename
        img.save(filepath, format="PNG", optimize=True)
        relative_url = f"/api/v1/try-on/vton/images/{filename}"
        logger.info(f"Saved distinct try-on asset [{view_type}]: {filepath}")
        return str(filepath), relative_url

    def get_asset_path(self, filename: str) -> Optional[Path]:
        """Looks up asset path across uploads and generated views."""
        target_gen = self.assets_dir / filename
        if target_gen.exists() and target_gen.is_file():
            return target_gen
        target_up = self.uploads_dir / filename
        if target_up.exists() and target_up.is_file():
            return target_up
        return None

    def delete_job_assets(self, job_id: str, person_image_path: Optional[str] = None) -> int:
        """
        Deletes all generated view assets and uploaded photograph associated with job_id.
        """
        deleted_count = 0
        # Delete generated view files
        for view in ["front", "side", "back"]:
            p = self.assets_dir / f"{job_id}_{view}.png"
            if p.exists():
                try:
                    p.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Could not delete {p}: {e}")

        # Delete uploaded person photo if provided
        if person_image_path:
            p_up = Path(person_image_path)
            if p_up.exists():
                try:
                    p_up.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Could not delete {p_up}: {e}")

        logger.info(f"Cleaned up {deleted_count} assets for job {job_id}")
        return deleted_count
