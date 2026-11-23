"""
WearWise Storage Provider Protocol
Abstract storage port for content-addressable binary asset persistence.
"""

from typing import Protocol, Tuple


class StorageProvider(Protocol):
    """Abstract port for asset storage operations."""
    
    def store_asset(self, asset_bytes: bytes, content_type: str = "model/gltf-binary") -> Tuple[str, str]:
        """
        Store raw bytes into content-addressable storage.
        Returns Tuple of (storage_uri, sha256_checksum).
        """
        ...

    def retrieve_asset(self, storage_uri: str) -> bytes:
        """Retrieve raw bytes from storage URI. Raises FileNotFoundError if missing."""
        ...

    def delete_asset(self, storage_uri: str) -> bool:
        """Physically unlinks asset from storage. Idempotent (returns True if removed or already absent)."""
        ...

    def asset_exists(self, storage_uri: str) -> bool:
        """Checks if asset exists at storage URI."""
        ...
