"""
WearWise Local File System Storage Provider
Implements StorageProvider protocol from app.domain.interfaces.storage.
Stores 3D GLB binary files using SHA-256 content-addressable digests.
"""

import hashlib
import os
from pathlib import Path
from typing import Tuple

from app.domain.interfaces.storage import StorageProvider


DEFAULT_ASSET_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "assets" / "glb"


class LocalStorageProvider:
    """
    Content-addressable file storage provider.
    Saves assets at: {base_dir}/{sha256}.glb
    """

    def __init__(self, base_dir: Path = DEFAULT_ASSET_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def store_asset(self, asset_bytes: bytes, content_type: str = "model/gltf-binary") -> Tuple[str, str]:
        """
        Store raw bytes into content-addressable storage.
        Returns Tuple of (storage_uri, sha256_checksum).
        """
        sha256 = hashlib.sha256(asset_bytes).hexdigest()
        ext = "glb" if "gltf" in content_type or "glb" in content_type else "bin"
        file_path = self.base_dir / f"{sha256}.{ext}"
        
        # Write atomically if not already present
        if not file_path.exists():
            temp_path = self.base_dir / f"{sha256}.{ext}.tmp"
            temp_path.write_bytes(asset_bytes)
            os.replace(temp_path, file_path)
            
        storage_uri = file_path.as_posix()
        return storage_uri, sha256

    def retrieve_asset(self, storage_uri: str) -> bytes:
        """Retrieve raw bytes from storage URI. Raises FileNotFoundError if missing."""
        path = Path(storage_uri)
        if not path.exists():
            raise FileNotFoundError(f"Asset not found at storage URI: {storage_uri}")
        return path.read_bytes()

    def delete_asset(self, storage_uri: str) -> bool:
        """Physically unlinks asset from storage. Idempotent."""
        path = Path(storage_uri)
        if path.exists():
            try:
                path.unlink()
                return True
            except OSError:
                return False
        return True

    def asset_exists(self, storage_uri: str) -> bool:
        """Checks if asset exists at storage URI."""
        return Path(storage_uri).exists()
