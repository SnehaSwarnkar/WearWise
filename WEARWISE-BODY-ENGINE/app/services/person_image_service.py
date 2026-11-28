"""
WearWise Person Image Service
Validates uploaded real-person photographs, enforces orientation normalization,
strips EXIF / device metadata for privacy, and rejects avatar renderings or invalid files.
"""

import hashlib
import io
import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

from PIL import Image, ImageOps

logger = logging.getLogger("wearwise.vton.person_image")

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MIN_FILE_SIZE_BYTES = 10 * 1024         # 10 KB
SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}


class ValidationError(Exception):
    pass


class PersonImageService:
    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir is None:
            from app.config import DATA_DIR
            self.storage_dir = DATA_DIR / "uploads" / "vton"
        else:
            self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def validate_and_process(
        self,
        image_bytes: bytes,
        filename: str,
        user_consent: bool,
    ) -> Dict[str, Any]:
        """
        Validates uploaded photograph:
          1. Confirms explicit user consent.
          2. Enforces file size limits (10KB to 10MB).
          3. Validates image MIME type and integrity using PIL.
          4. Normalizes orientation via EXIF transpose.
          5. Strips EXIF and personal device metadata.
          6. Verifies dimensions and rejects avatar/mannequin synthetic artifacts.
          7. Computes cryptographic content hash (SHA-256).
          8. Saves clean photograph to protected storage.
        """
        if not user_consent:
            raise ValidationError(
                "Explicit consent is required to process your photograph for virtual try-on."
            )

        file_size = len(image_bytes)
        if file_size < MIN_FILE_SIZE_BYTES:
            raise ValidationError(
                "Image file is too small or corrupted. Please upload a clear photo of at least 10KB."
            )
        if file_size > MAX_FILE_SIZE_BYTES:
            raise ValidationError(
                "Image exceeds maximum limit of 10MB. Please upload a smaller photograph."
            )

        try:
            raw_image = Image.open(io.BytesIO(image_bytes))
            raw_image.verify()
            # Reopen after verify
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ValidationError(f"Invalid or corrupted image file: {str(e)}")

        format_name = image.format.upper() if image.format else ""
        if format_name not in SUPPORTED_FORMATS:
            raise ValidationError(
                f"Unsupported image format: '{format_name}'. Allowed formats are JPEG, PNG, and WebP."
            )

        width, height = image.size
        if width < 256 or height < 256:
            raise ValidationError(
                f"Image resolution {width}x{height} is too low. Minimum required resolution is 256x256."
            )

        # 4. Normalize orientation from EXIF metadata
        try:
            image = ImageOps.exif_transpose(image)
        except Exception:
            pass

        # 5. Strip EXIF and personal device metadata by copying raw pixels into a fresh RGB image
        if image.mode != "RGB":
            image = image.convert("RGB")
        clean_image = Image.new("RGB", image.size)
        clean_image.paste(image)
        image = clean_image

        # 6. Avatar / Mannequin heuristic rejection
        # Synthetic Anny avatar renderings have very uniform gray backgrounds (e.g. #0a0e17)
        # and distinct palette distributions.
        colors = image.getcolors(maxcolors=256)
        if colors is not None and len(colors) < 16:
            raise ValidationError(
                "Uploaded image appears to be a synthetic avatar or flat graphic. "
                "Photo Try-On requires a real-person photograph."
            )

        # 7. Compute SHA-256 content hash of EXIF-free cleaned image
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="JPEG", quality=92, optimize=True)
        cleaned_bytes = output_buffer.getvalue()

        sha256_hash = hashlib.sha256(cleaned_bytes).hexdigest()
        saved_filename = f"person_{sha256_hash[:16]}.jpg"
        saved_path = self.storage_dir / saved_filename

        with open(saved_path, "wb") as f:
            f.write(cleaned_bytes)

        logger.info(f"Validated and stored clean person photograph: {saved_path} (hash: {sha256_hash[:8]}...)")

        return {
            "sha256_hash": sha256_hash,
            "file_path": str(saved_path),
            "file_name": saved_filename,
            "width": image.width,
            "height": image.height,
            "size_bytes": len(cleaned_bytes),
            "relative_url": f"/api/v1/try-on/vton/images/{saved_filename}",
        }

    def delete_photo(self, file_path_str: str) -> bool:
        """Deletes photograph from private disk storage."""
        try:
            p = Path(file_path_str)
            if p.exists() and p.is_file():
                p.unlink()
                logger.info(f"Deleted private person photo: {file_path_str}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete photo {file_path_str}: {e}")
        return False
