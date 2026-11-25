"""
WearWise Virtual Try-On Provider Abstraction
============================================
Defines an honest AI Virtual Try-On provider interface and external adapter boundary:
  - HonestVTONProviderAdapter: Supports FASHN AI API v1 (`VTON_PROVIDER=fashn` + `FASHN_API_KEY`)
    and generic external VTON HTTP endpoints (`VTON_API_URL` + `VTON_API_KEY`).
  - Fails closed with VTONProviderUnavailableError when no external provider is configured
    and local workstation VRAM (< 12 GB) cannot host local diffusion inference.
  - Never fabricates geometric or colored Pillow overlays as AI Virtual Try-On.
"""

import abc
import base64
import io
import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

import httpx
import torch
from PIL import Image

logger = logging.getLogger("wearwise.vton.provider")

DEFAULT_FASHN_RUN_URL = "https://api.fashn.ai/v1/run"
DEFAULT_FASHN_STATUS_URL = "https://api.fashn.ai/v1/status/{prediction_id}"


class VTONProviderUnavailableError(RuntimeError):
    """Raised honestly when no external VTON provider or compatible local GPU model is available."""


def _map_wearwise_category_to_fashn(category: str) -> str:
    c = (category or "").strip().lower()
    if any(k in c for k in ("skirt", "jean", "trouser", "pant", "bottom", "denim")):
        return "bottoms"
    if any(k in c for k in ("dress", "one-piece", "jumpsuit")):
        return "one-pieces"
    if any(k in c for k in ("shirt", "top", "tee", "jacket", "hoodie", "polo")):
        return "tops"
    return "auto"


class BaseVTONProvider(abc.ABC):
    @abc.abstractmethod
    def is_ready(self) -> Tuple[bool, str]:
        """Returns (is_available, human_readable_reason_if_unavailable)."""

    @abc.abstractmethod
    def get_provider_metadata(self) -> Dict[str, Any]:
        """Returns technical telemetry, hardware checks, licensing, and honest availability status."""

    @abc.abstractmethod
    def generate_multiview(
        self,
        person_image_path: str,
        garment_sku: str,
        garment_metadata: Dict[str, Any],
    ) -> Dict[str, Image.Image]:
        """Executes AI virtual try-on and returns available generated view images (e.g. 'front')."""


class HonestVTONProviderAdapter(BaseVTONProvider):
    """
    Honest Virtual Try-On provider boundary supporting:
      1. FASHN AI API v1 (`VTON_PROVIDER=fashn` with `FASHN_API_KEY` or `VTON_API_KEY`)
      2. External VTON HTTP API (`VTON_API_URL` with optional `VTON_API_KEY`)
    Reports explicit `provider_unavailable` whenever unconfigured or unhealthy.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        provider_name: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        self.explicit_api_url = api_url
        self.explicit_api_key = api_key
        self.explicit_provider_name = provider_name
        self.explicit_timeout = timeout_seconds
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.vram_gb = (
            torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            if torch.cuda.is_available()
            else 0.0
        )

    def _resolve_config(self) -> Dict[str, Any]:
        mode_override = os.getenv("VTON_PROVIDER_MODE", "auto").strip().lower()
        provider_type = os.getenv("VTON_PROVIDER", "").strip().lower()
        fashn_key = os.getenv("FASHN_API_KEY", "").strip()
        api_key = (
            self.explicit_api_key
            if self.explicit_api_key is not None
            else (os.getenv("VTON_API_KEY", "").strip() or fashn_key)
        )
        api_url = (
            self.explicit_api_url
            if self.explicit_api_url is not None
            else os.getenv("VTON_API_URL", "").strip()
        )
        timeout = float(
            self.explicit_timeout
            if self.explicit_timeout is not None
            else os.getenv("VTON_TIMEOUT_SECONDS", "60")
        )

        if not provider_type and fashn_key:
            provider_type = "fashn"
        elif not provider_type and api_url:
            provider_type = "external_http"

        if provider_type == "fashn" and not api_url:
            api_url = DEFAULT_FASHN_RUN_URL

        provider_name = (
            self.explicit_provider_name
            if self.explicit_provider_name is not None
            else os.getenv(
                "VTON_PROVIDER_NAME",
                "FASHN AI API v1" if provider_type == "fashn" else "External AI VTON API",
            )
        ).strip()

        return {
            "mode_override": mode_override,
            "provider_type": provider_type,
            "api_url": api_url,
            "api_key": api_key,
            "provider_name": provider_name,
            "timeout_seconds": timeout,
        }

    def is_ready(self) -> Tuple[bool, str]:
        cfg = self._resolve_config()
        if cfg["mode_override"] == "disabled":
            return False, (
                "Photo Try-On is currently paused in this environment. "
                "You can still explore compatible items in Interactive 3D Try-On."
            )
        if cfg["provider_type"] == "fashn":
            if cfg["api_key"]:
                return True, ""
            return False, (
                "FASHN AI VTON provider is selected, but FASHN_API_KEY / VTON_API_KEY is not configured."
            )
        if cfg["api_url"]:
            return True, ""
        return False, (
            "Image Try-On service is currently unavailable until an external AI try-on provider "
            "(such as FASHN AI API or Google Vertex AI Virtual Try-On) is connected via environment configuration. "
            f"Local GPU ({self.vram_gb:.1f} GB VRAM) is below the 12 GB requirement for local diffusion inference."
        )

    def get_provider_metadata(self) -> Dict[str, Any]:
        cfg = self._resolve_config()
        ready, reason = self.is_ready()
        configured = bool(
            cfg["mode_override"] != "disabled"
            and ((cfg["provider_type"] == "fashn" and cfg["api_key"]) or bool(cfg["api_url"]))
        )
        return {
            "configured": configured,
            "healthy": ready,
            "available": ready,
            "status": "ready" if ready else "provider_unavailable",
            "provider_type": cfg["provider_type"] or "unconfigured",
            "provider_name": cfg["provider_name"] if ready else "unconfigured",
            "unavailable_reason": None if ready else reason,
            "activation_requirements": {
                "recommended_primary": "FASHN AI API v1 (commercial license, ~$0.075/image, 3-day deletion, no training)",
                "recommended_india_billing": "Google Vertex AI virtual-try-on-001 (Google Cloud India Pvt Ltd INR billing + UPI + GST)",
                "env_vars_fashn": ["VTON_PROVIDER=fashn", "FASHN_API_KEY"],
                "env_vars_custom_http": ["VTON_API_URL", "VTON_API_KEY"],
            },
            "requires_external_provider": True,
            "device": self.device,
            "vram_available_gb": round(self.vram_gb, 2),
            "generated_views": ["front"] if ready else [],
            "fashn_v1_5": {
                "license": "Apache-2.0",
                "scope": "Frontal VTON only",
                "minimum_vram_gb": 12.0,
                "local_vram_gb": round(self.vram_gb, 2),
                "is_hardware_sufficient": self.vram_gb >= 12.0,
                "status": (
                    "Hardware sufficient"
                    if self.vram_gb >= 12.0
                    else f"Hardware constrained ({self.vram_gb:.1f} GB VRAM available; requires 12 GB fp16)"
                ),
            },
            "wacv_2026_multiview": {
                "paper": "Pose-Diverse Multi-View Virtual Try-on from a Single Frontal Image via Diffusion Transformer",
                "authors": "Seonghee Han, Minchang Chung, Gyeongsu Cho, Kyungdon Joo, Taehwan Kim",
                "conference": "WACV 2026",
                "public_checkpoint_released": False,
                "status": "Academic publication verified; public model weights pending author release",
            },
        }

    def _run_fashn_prediction(
        self,
        cfg: Dict[str, Any],
        person_bytes: bytes,
        garment_metadata: Dict[str, Any],
    ) -> Dict[str, Image.Image]:
        garment_url = garment_metadata.get("front_image_url") or ""
        if not garment_url:
            raise VTONProviderUnavailableError(
                "Garment front photo URL is required for external Photo Try-On."
            )
        person_data_uri = "data:image/jpeg;base64," + base64.b64encode(person_bytes).decode("ascii")
        payload = {
            "model_name": os.getenv("FASHN_MODEL_NAME", "tryon-v1.6"),
            "inputs": {
                "model_image": person_data_uri,
                "garment_image": garment_url,
                "category": _map_wearwise_category_to_fashn(garment_metadata.get("category", "tops")),
            },
        }
        headers = {
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json",
        }
        deadline = time.time() + cfg["timeout_seconds"]
        try:
            with httpx.Client(timeout=min(30.0, cfg["timeout_seconds"])) as client:
                run_resp = client.post(cfg["api_url"], json=payload, headers=headers)
                run_resp.raise_for_status()
                run_body = run_resp.json()
                pred_id = run_body.get("id")
                if not pred_id:
                    raise VTONProviderUnavailableError("FASHN API did not return a prediction ID.")
                status_url_tpl = os.getenv("FASHN_STATUS_URL", DEFAULT_FASHN_STATUS_URL)
                status_url = status_url_tpl.format(prediction_id=pred_id)
                while time.time() < deadline:
                    st_resp = client.get(status_url, headers=headers)
                    st_resp.raise_for_status()
                    st_body = st_resp.json()
                    st = st_body.get("status")
                    if st == "completed":
                        outputs = st_body.get("output") or []
                        if not outputs:
                            raise VTONProviderUnavailableError("FASHN prediction completed without output image.")
                        img_resp = client.get(outputs[0])
                        img_resp.raise_for_status()
                        return {"front": Image.open(io.BytesIO(img_resp.content)).convert("RGB")}
                    if st in ("failed", "canceled"):
                        err = st_body.get("error") or "FASHN inference failed"
                        raise VTONProviderUnavailableError(f"External VTON generation failed: {err}")
                    time.sleep(1.5)
        except httpx.HTTPError as exc:
            logger.error("FASHN API call failed: %s", exc)
            raise VTONProviderUnavailableError(
                f"Connected FASHN AI try-on provider failed cleanly ({exc})."
            ) from exc

        raise VTONProviderUnavailableError("External AI try-on request timed out before returning an image.")

    def generate_multiview(
        self,
        person_image_path: str,
        garment_sku: str,
        garment_metadata: Dict[str, Any],
    ) -> Dict[str, Image.Image]:
        cfg = self._resolve_config()
        ready, reason = self.is_ready()
        if not ready:
            raise VTONProviderUnavailableError(reason)

        with open(person_image_path, "rb") as f:
            person_bytes = f.read()

        if cfg["provider_type"] == "fashn":
            return self._run_fashn_prediction(cfg, person_bytes, garment_metadata)

        headers: Dict[str, str] = {}
        if cfg["api_key"]:
            headers["Authorization"] = f"Bearer {cfg['api_key']}"

        payload = {
            "garment_sku": garment_sku,
            "garment_title": garment_metadata.get("title", garment_sku),
            "category": garment_metadata.get("category", "tops"),
            "garment_image_url": garment_metadata.get("front_image_url") or "",
            "person_image_base64": base64.b64encode(person_bytes).decode("ascii"),
        }

        try:
            with httpx.Client(timeout=cfg["timeout_seconds"]) as client:
                resp = client.post(cfg["api_url"], json=payload, headers=headers)
                resp.raise_for_status()
                body = resp.json()
        except httpx.HTTPError as exc:
            logger.error("External VTON API call failed for %s: %s", garment_sku, exc)
            raise VTONProviderUnavailableError(
                f"Connected AI try-on provider failed to respond cleanly ({exc}). Please retry shortly."
            ) from exc

        views_out: Dict[str, Image.Image] = {}
        raw_views = body.get("views") if isinstance(body, dict) else None
        if isinstance(raw_views, dict):
            candidates = raw_views
        elif isinstance(body, dict) and body.get("image_base64"):
            candidates = {"front": body["image_base64"]}
        else:
            candidates = {}

        for view_key in ("front", "side", "back"):
            encoded = candidates.get(view_key)
            if not encoded:
                continue
            if isinstance(encoded, str) and encoded.startswith("data:"):
                _, encoded = encoded.split(",", 1)
            img_bytes = base64.b64decode(encoded)
            views_out[view_key] = Image.open(io.BytesIO(img_bytes)).convert("RGB")

        if "front" not in views_out:
            raise VTONProviderUnavailableError(
                "External VTON provider did not return a valid rendered image."
            )
        return views_out
