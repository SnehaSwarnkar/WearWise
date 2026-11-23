"""
WearWise Avatar Orchestration Application Service
Bridges Profile Revisions -> BICE Mapping -> NAVER Anny v0.6.2 Avatar Engine ->
Content-Addressable Asset Storage -> AnthropometryEngine Measurement Extraction -> DB Persistence.
Strictly verifies profile ownership.
"""

import time
import uuid
from decimal import Decimal
from typing import Optional, Dict, Any, Tuple

from sqlalchemy.orm import Session

from app.domain.entities.avatar import AvatarShapeSpec
from app.domain.taxonomies.garment import PresentationGender
from app.bice.mapping import map_controls_to_regional_scales
from app.avatar_engine.adapters.anny_adapter import AnnyAdapter
from app.anthropometry.engine import AnthropometryEngine, SUPPORTED_CORE_MEASUREMENTS
from app.storage.local import LocalStorageProvider
from app.repositories.profile_repository import ProfileRepository
from app.repositories.avatar_repository import AvatarRepository
from app.db.models import AvatarAssetModel, BodyMeasurementModel
from app.services.errors import NotFoundError, ForbiddenError, ServiceError


class AvatarOrchestrationService:
    """
    Coordinates 3D mesh generation, asset storage, and anthropometric extraction.
    """

    def __init__(
        self,
        db: Session,
        adapter: Optional[AnnyAdapter] = None,
        storage: Optional[LocalStorageProvider] = None,
        anthropometry_engine: Optional[AnthropometryEngine] = None,
    ):
        self.db = db
        self.profile_repo = ProfileRepository(db)
        self.avatar_repo = AvatarRepository(db)
        self.storage = storage or LocalStorageProvider()
        self.anthropometry_engine = anthropometry_engine or AnthropometryEngine()

        if adapter is not None:
            self.adapter = adapter
        else:
            self.adapter = AnnyAdapter(device="cpu")
            self.adapter.initialize()

    def generate_avatar_for_profile(
        self,
        profile_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end avatar generation for the active profile revision:
        1. Verifies profile ownership.
        2. Compiles AvatarShapeSpec from active stature, gender, and shape controls.
        3. Generates 3D mesh using NAVER Anny adapter.
        4. Validates mesh manifold properties and exports binary GLB.
        5. Saves GLB to content-addressable storage using SHA-256 digest.
        6. Extracts anthropometric measurements using AnthropometryEngine.
        7. Persists configuration, asset record, and updates active measurements.
        """
        profile = self.profile_repo.get_profile(profile_id)
        if not profile:
            raise NotFoundError(f"Profile {profile_id} not found.")

        if profile.user_id != requesting_user_id:
            raise ForbiddenError(
                "Access denied: You do not have permission to generate an avatar for this profile.",
                code="OWNERSHIP_VIOLATION",
            )

        latest_rev = self.profile_repo.get_latest_revision(profile_id)
        if not latest_rev:
            raise NotFoundError(f"Profile {profile_id} has no active revisions.")

        # 1. Compile shape controls
        controls_dict = {
            "shoulder_width": 0.50,
            "chest_fullness": 0.50,
            "belly_fullness": 0.50,
            "waist_definition": 0.50,
            "arm_fullness": 0.50,
            "hip_fullness": 0.50,
            "thigh_fullness": 0.50,
            "calf_fullness": 0.50,
        }
        if latest_rev.shape_controls:
            sc = latest_rev.shape_controls
            controls_dict.update({
                "shoulder_width": float(sc.shoulder_width),
                "chest_fullness": float(sc.chest_fullness),
                "belly_fullness": float(sc.belly_fullness),
                "waist_definition": float(sc.waist_definition),
                "arm_fullness": float(sc.arm_fullness),
                "hip_fullness": float(sc.hip_fullness),
                "thigh_fullness": float(sc.thigh_fullness),
                "calf_fullness": float(sc.calf_fullness),
            })

        # 2. Map semantic controls to regional scales
        regional_scales = map_controls_to_regional_scales(controls_dict)

        # 3. Construct AvatarShapeSpec
        gender_enum = PresentationGender(profile.presentation_gender)
        target_stature = float(profile.stature_cm)
        shape_spec = AvatarShapeSpec(
            spec_version="1.0.0",
            presentation=gender_enum,
            target_stature_cm=target_stature,
            target_measurements={},
            regional_scales=regional_scales,
            semantic_controls=controls_dict,
        )

        # 4. Generate avatar mesh with Anny adapter
        start_time = time.perf_counter()
        mesh = self.adapter.generate_avatar(shape_spec)
        validation_report = self.adapter.validate_mesh(mesh)
        glb_bytes = self.adapter.export_glb(mesh)
        duration_ms = Decimal(f"{(time.perf_counter() - start_time) * 1000.0:.2f}")

        # 5. Store GLB in content-addressable storage
        storage_uri, sha256_checksum = self.storage.store_asset(glb_bytes, content_type="model/gltf-binary")

        # 6. Extract anthropometric measurements
        lp = self.adapter.get_landmark_provider(mesh=mesh)
        extraction_res = self.anthropometry_engine.extract_all(
            mesh_data=mesh,
            landmark_provider=lp,
            avatar_id=f"profile_{profile.id}_rev_{latest_rev.revision_number}",
            measurement_codes=SUPPORTED_CORE_MEASUREMENTS,
        )

        # 7. Persist configuration and asset metadata
        engine_meta = self.adapter.get_metadata()
        shape_spec_serializable = {
            "spec_version": shape_spec.spec_version,
            "presentation": shape_spec.presentation.value,
            "target_stature_cm": shape_spec.target_stature_cm,
            "semantic_controls": shape_spec.semantic_controls,
            "regional_scales": {
                k: {"scale_x": v.scale_x, "scale_y": v.scale_y, "scale_z": v.scale_z}
                for k, v in shape_spec.regional_scales.items()
            },
        }

        config_model = self.avatar_repo.create_avatar_configuration(
            revision_id=latest_rev.id,
            engine_name=engine_meta.engine_name,
            engine_version=engine_meta.engine_version,
            shape_spec_json=shape_spec_serializable,
            adapter_metadata_json={
                "device_type": engine_meta.device_type,
                "supported_capabilities": [c.value if hasattr(c, "value") else str(c) for c in engine_meta.supported_capabilities],
                "mesh_is_valid": validation_report.is_valid,
                "is_watertight": validation_report.is_watertight,
            },
        )

        asset_model = self.avatar_repo.create_avatar_asset(
            config_id=config_model.id,
            format_type="glb",
            size_bytes=len(glb_bytes),
            sha256_checksum=sha256_checksum,
            storage_uri=storage_uri,
            generation_duration_ms=duration_ms,
            vertex_count=len(mesh.vertices),
            is_valid_manifold=validation_report.is_valid,
        )

        # 8. Update active geometry-extracted measurements on the revision
        extracted_summary = {}
        for code, rec in extraction_res.records.items():
            if rec.measurement and rec.diagnostic.status_code == "SUCCESS":
                val = rec.measurement.value_cm
                state = rec.measurement.assessment_state.value
                extracted_summary[code] = {
                    "value_cm": float(val),
                    "acquisition_method": "geometry_extracted",
                    "validation_state": "internally_consistent",
                    "lifecycle_status": "active",
                    "assessment_state": state,
                    "algorithm_version": "1.2-mesh-plane-graph",
                }

                # Update or insert into body_measurements
                existing_m = next((m for m in latest_rev.measurements if m.measurement_code == code), None)
                if existing_m:
                    existing_m.value_cm = val
                    existing_m.acquisition_method = "geometry_extracted"
                    existing_m.validation_state = "internally_consistent"
                    existing_m.assessment_state = state
                else:
                    new_m = BodyMeasurementModel(
                        revision_id=latest_rev.id,
                        measurement_code=code,
                        value_cm=val,
                        unit="cm",
                        acquisition_method="geometry_extracted",
                        validation_state="internally_consistent",
                        lifecycle_status="active",
                        assessment_state=state,
                        landmark_convention=rec.measurement.landmark_convention,
                        tolerance_cm=rec.measurement.tolerance_cm,
                        reliability_weight=rec.measurement.reliability_weight,
                    )
                    self.db.add(new_m)

        self.db.flush()

        return {
            "avatar_id": str(asset_model.id),
            "profile_id": str(profile.id),
            "profile_revision": latest_rev.revision_number,
            "asset_url": f"/api/v1/avatar/assets/{asset_model.id}.glb",
            "format": "glb",
            "size_bytes": len(glb_bytes),
            "sha256_checksum": sha256_checksum,
            "generation_duration_ms": float(duration_ms),
            "vertex_count": len(mesh.vertices),
            "is_valid_manifold": validation_report.is_valid,
            "extracted_measurements": extracted_summary,
            "status": "completed",
        }

    def get_avatar_asset(self, asset_id: uuid.UUID, requesting_user_id: uuid.UUID) -> Tuple[AvatarAssetModel, bytes]:
        """
        Retrieves asset record and binary payload after verifying profile ownership.
        """
        asset = self.avatar_repo.get_avatar_asset(asset_id)
        if not asset:
            raise NotFoundError(f"Avatar asset {asset_id} not found.")

        # Check ownership: configuration -> revision -> profile -> user_id
        owner_user_id = asset.configuration.revision.profile.user_id
        if owner_user_id != requesting_user_id:
            raise ForbiddenError(
                "Access denied: You do not have permission to view or retrieve this avatar asset.",
                code="OWNERSHIP_VIOLATION",
            )

        asset_bytes = self.storage.retrieve_asset(asset.storage_uri)
        return asset, asset_bytes

    def get_avatar_status(self, asset_id: uuid.UUID, requesting_user_id: uuid.UUID) -> Dict[str, Any]:
        """Retrieves asset status and validation metadata after checking ownership."""
        asset = self.avatar_repo.get_avatar_asset(asset_id)
        if not asset:
            raise NotFoundError(f"Avatar asset {asset_id} not found.")

        owner_user_id = asset.configuration.revision.profile.user_id
        if owner_user_id != requesting_user_id:
            raise ForbiddenError("Access denied: You do not own this avatar asset.", code="OWNERSHIP_VIOLATION")

        return {
            "avatar_id": str(asset.id),
            "profile_id": str(asset.configuration.revision.profile_id),
            "format": asset.format,
            "size_bytes": asset.size_bytes,
            "sha256_checksum": asset.sha256_checksum,
            "generation_duration_ms": float(asset.generation_duration_ms),
            "vertex_count": asset.vertex_count,
            "is_valid_manifold": asset.is_valid_manifold,
            "status": "completed",
            "engine_metadata": asset.configuration.adapter_metadata_json,
        }
