"""
WearWise NAVER Anny v0.6.2 Adapter Implementation
Strictly encapsulates all NAVER Anny, PyTorch, and low-level morph dependencies.
Conforms strictly to AvatarEngine, LandmarkProvider, and ShapeEvaluationPort protocols.
"""

from dataclasses import dataclass
import io
import math
import time
from typing import Dict, List, Optional, Set, Tuple, Union, Any
import numpy as np
import torch
import trimesh

import anny

from app.domain.entities.avatar import (
    AvatarShapeSpec,
    MeshData,
    LandmarkData,
    RegionalShapeScale,
    RegionalDisplacementSummary,
    ShapeEvaluationResult,
)
from app.domain.taxonomies.garment import PresentationGender
from app.domain.interfaces.avatar import (
    AvatarEngine,
    LandmarkProvider,
    ShapeEvaluationPort,
    MeshValidationReport,
    EngineMetadata,
)
from app.avatar_engine.exceptions import (
    AvatarEngineError,
    EngineNotReadyError,
    InvalidParameterError,
    MeshDeformationError,
    GLBExportError,
)

# Canonical anatomical region names in WearWise
ALL_ANATOMICAL_REGIONS: Tuple[str, ...] = (
    "shoulders",
    "torso_chest",
    "waist_abdomen",
    "arms",
    "hips",
    "thighs",
    "calves",
)

# Canonical landmark vertex index mapping on Anny topology (13,718 vertices)
# Reconciled per Anthropometry Specification Rev 1.2.1 Landmark Compatibility Audit
ANNY_CANONICAL_LANDMARKS: Dict[str, Tuple[int, str]] = {
    "acromion_left": (8260, "shoulders"),
    "acromion_right": (1604, "shoulders"),
    "cervicale_c7": (1402, "torso_chest"),
    "suprasternale": (1600, "torso_chest"),
    "sternum_lower": (3930, "torso_chest"),
    "umbilicus": (4044, "waist_abdomen"),
    "waist_level": (4198, "waist_abdomen"),
    "sacrum_mid": (4313, "hips"),
    "trochanterion_left": (11025, "hips"),
    "trochanterion_right": (4423, "hips"),
}


class AnnyLandmarkProvider:
    """
    Implements LandmarkProvider without exposing Anny internal topology to external consumers.
    Computes 3D coordinates in meters from the bound mesh, specified mesh, or active adapter state.
    """
    def __init__(self, adapter: "AnnyAdapter", mesh: Optional[MeshData] = None) -> None:
        self._adapter = adapter
        self._mesh = mesh
        self._region_masks: Dict[str, Set[int]] = self._build_region_masks()

    def _build_region_masks(self) -> Dict[str, Set[int]]:
        """Precomputes anatomical region vertex masks based on bone weights and template coordinates."""
        model = self._adapter.get_model()
        weights = model.dense_vertex_bone_weights.detach().cpu().numpy()
        v = model.template_vertices.detach().cpu().numpy()
        bones = list(model.bone_labels)

        def bone_indices(patterns: List[str]) -> List[int]:
            return [i for i, b in enumerate(bones) if any(p in b for p in patterns)]

        arm_b = bone_indices(["upperarm", "lowerarm", "wrist", "hand", "thumb", "index", "middle", "ring", "pinky"])
        thigh_b = bone_indices(["upperleg"])
        calf_b = bone_indices(["lowerleg", "foot", "toe"])
        shoulder_b = bone_indices(["clavicle", "shoulder"])
        chest_b = bone_indices(["spine03", "spine04", "spine05"])
        waist_b = bone_indices(["spine01", "spine02"])
        hip_b = bone_indices(["pelvis", "root"])

        def make_mask(b_idxs: List[int], z_min: Optional[float] = None, z_max: Optional[float] = None, min_w: float = 0.05) -> Set[int]:
            cond = weights[:, b_idxs].sum(axis=1) > min_w
            if z_min is not None:
                cond = cond & (v[:, 2] >= z_min)
            if z_max is not None:
                cond = cond & (v[:, 2] <= z_max)
            return set(np.where(cond)[0].tolist())

        return {
            "shoulders": make_mask(shoulder_b, z_min=0.30),
            "torso_chest": make_mask(chest_b, z_min=0.15, z_max=0.48),
            "waist_abdomen": make_mask(waist_b, z_min=-0.05, z_max=0.25, min_w=0.02),
            "arms": make_mask(arm_b),
            "hips": make_mask(hip_b, z_min=-0.15, z_max=0.05),
            "thighs": make_mask(thigh_b, z_min=-0.50, z_max=-0.02),
            "calves": make_mask(calf_b, z_max=-0.40),
        }

    def get_landmark(self, landmark_code: str) -> Optional[LandmarkData]:
        if landmark_code not in ANNY_CANONICAL_LANDMARKS:
            return None
        pt = self.get_landmark_point_m(landmark_code)
        if pt is None:
            return None
        _, region = ANNY_CANONICAL_LANDMARKS[landmark_code]
        return LandmarkData(
            landmark_code=landmark_code,
            point_3d_m=(float(pt[0]), float(pt[1]), float(pt[2])),
            anatomical_region=region,
        )

    def get_landmark_point_m(self, landmark_code: str, mesh: Optional[MeshData] = None) -> Optional[np.ndarray]:
        if landmark_code not in ANNY_CANONICAL_LANDMARKS:
            return None
        v_idx, _ = ANNY_CANONICAL_LANDMARKS[landmark_code]
        active_mesh = mesh or self._mesh or self._adapter.get_last_mesh()
        if active_mesh is not None:
            return active_mesh.vertices[v_idx].copy()
        # Fallback to neutral template
        model = self._adapter.get_model()
        return model.template_vertices[v_idx].detach().cpu().numpy().copy()

    def get_all_landmarks(self) -> Dict[str, LandmarkData]:
        result = {}
        for code in ANNY_CANONICAL_LANDMARKS:
            lm = self.get_landmark(code)
            if lm is not None:
                result[code] = lm
        return result

    def get_region_vertex_mask(self, region_code: str) -> Set[int]:
        if region_code not in self._region_masks:
            return set()
        return set(self._region_masks[region_code])


class AnnyShapeEvaluationPort:
    """
    Implements ShapeEvaluationPort for geometric locality evaluation and RMSR/PVSR feedback.
    Enforces near-zero target signal policy (threshold = 1e-4 m).
    """
    def __init__(self, adapter: "AnnyAdapter") -> None:
        self._adapter = adapter
        self.metric_version = "1.2.1-rmsr-pvsr"
        self.target_signal_threshold_m = 1e-4  # 0.1 mm in meters

    def evaluate_shape(
        self,
        shape_spec: AvatarShapeSpec,
        target_region: str,
        requested_regions: List[str],
    ) -> ShapeEvaluationResult:
        # 1. Generate candidate mesh
        cand_mesh = self._adapter.generate_avatar(shape_spec)

        # 2. Generate reference baseline with identical presentation and stature
        ref_mesh = self._adapter.generate_baseline(
            presentation=shape_spec.presentation,
            stature_m=shape_spec.target_stature_cm / 100.0,
        )

        # 3. Compute vertex displacements in METERS
        disp_vectors = cand_mesh.vertices - ref_mesh.vertices
        disp_magnitudes = np.linalg.norm(disp_vectors, axis=-1)  # shape (N,)

        # 4. Evaluate regional summaries
        lp = self._adapter.get_landmark_provider()
        regional_summaries: Dict[str, RegionalDisplacementSummary] = {}

        for reg in requested_regions:
            mask = lp.get_region_vertex_mask(reg)
            if not mask:
                regional_summaries[reg] = RegionalDisplacementSummary(
                    region_code=reg,
                    mean_displacement_m=0.0,
                    max_displacement_m=0.0,
                    vertex_count=0,
                )
                continue

            indices = list(mask)
            reg_disps = disp_magnitudes[indices]
            mean_d = float(np.mean(reg_disps)) if len(reg_disps) > 0 else 0.0
            max_d = float(np.max(reg_disps)) if len(reg_disps) > 0 else 0.0
            regional_summaries[reg] = RegionalDisplacementSummary(
                region_code=reg,
                mean_displacement_m=mean_d,
                max_displacement_m=max_d,
                vertex_count=len(indices),
            )

        # Target regional statistics
        target_summary = regional_summaries.get(target_region)
        target_mean_m = target_summary.mean_displacement_m if target_summary else 0.0
        target_max_m = target_summary.max_displacement_m if target_summary else 0.0

        # Non-target regional statistics
        non_target_means = [
            s.mean_displacement_m
            for r, s in regional_summaries.items()
            if r != target_region
        ]
        non_target_maxes = [
            s.max_displacement_m
            for r, s in regional_summaries.items()
            if r != target_region
        ]

        max_non_target_mean_m = max(non_target_means) if non_target_means else 0.0
        max_non_target_peak_m = max(non_target_maxes) if non_target_maxes else 0.0

        # Structural plausibility check
        is_plausible = bool(
            np.isfinite(disp_magnitudes).all() and not np.isnan(disp_magnitudes).any()
        )

        # 5. Near-Zero Target Signal Evaluation Policy
        if target_mean_m < self.target_signal_threshold_m:
            return ShapeEvaluationResult(
                metric_version=self.metric_version,
                evaluation_status="insufficient_target_signal",
                regional_displacements=regional_summaries,
                target_region_mean_m=target_mean_m,
                max_non_target_mean_m=max_non_target_mean_m,
                rmsr=None,
                pvsr=None,
                is_plausible=False,
                diagnostic_notes=(
                    f"Target displacement {target_mean_m*1000.0:.4f} mm is below evaluation threshold "
                    f"({self.target_signal_threshold_m*1000.0:.2f} mm). Step marked rejected."
                ),
            )

        # Compute RMSR and PVSR
        rmsr = max_non_target_mean_m / target_mean_m
        pvsr = max_non_target_peak_m / target_max_m if target_max_m > 0.0 else 0.0

        return ShapeEvaluationResult(
            metric_version=self.metric_version,
            evaluation_status="success",
            regional_displacements=regional_summaries,
            target_region_mean_m=target_mean_m,
            max_non_target_mean_m=max_non_target_mean_m,
            rmsr=rmsr,
            pvsr=pvsr,
            is_plausible=is_plausible,
            diagnostic_notes=(
                f"Evaluated RMSR={rmsr:.4f}, PVSR={pvsr:.4f}. "
                f"Target mean={target_mean_m*1000.0:.2f} mm, max spillover={max_non_target_mean_m*1000.0:.2f} mm."
            ),
        )


class AnnyAdapter:
    """
    Concrete adapter for NAVER Anny v0.6.2.
    Strictly encapsulates PyTorch CPU tensors, LBS skinning, and parameter translation.
    Conforms to AvatarEngine protocol.
    """
    def __init__(self, device: str = "cpu") -> None:
        self.device = device
        self._model: Optional[anny.Anny] = None
        self._pose_params: Optional[torch.Tensor] = None
        self._ready: bool = False
        self._faces: Optional[np.ndarray] = None
        self._landmark_provider: Optional[AnnyLandmarkProvider] = None
        self._shape_evaluation_port: Optional[AnnyShapeEvaluationPort] = None
        self._last_mesh: Optional[MeshData] = None

    def initialize(self) -> bool:
        """
        Loads Anny model onto CPU using Linear Blend Skinning (lbs) to avoid Windows warp.dll issue.
        Idempotent: if already initialized, returns True immediately.
        """
        if self._ready and self._model is not None:
            return True

        t0 = time.perf_counter()
        # Initialize native Anny with lbs skinning
        self._model = anny.Anny(
            local_changes="default",
            skinning_method="lbs",
        ).to(device=self.device, dtype=torch.float32)

        # Precompute identity pose parameters: 104 bones in Anny rig
        self._pose_params = torch.eye(
            4, device=self.device, dtype=torch.float32
        )[None, None].repeat(1, self._model.bone_count, 1, 1)

        # Precompute faces
        self._faces = (
            self._model.faces.detach().cpu().numpy().astype(np.int32)
            if hasattr(self._model, "faces")
            else self._model.get_faces().detach().cpu().numpy().astype(np.int32)
        )

        self._ready = True

        # Initialize sub-providers
        self._landmark_provider = AnnyLandmarkProvider(self)
        self._shape_evaluation_port = AnnyShapeEvaluationPort(self)

        return True

    def is_ready(self) -> bool:
        """Returns True if the engine is initialized and ready for forward inference."""
        return self._ready and self._model is not None

    def get_model(self) -> anny.Anny:
        """Internal accessor for Anny model."""
        if not self.is_ready():
            raise EngineNotReadyError("Anny model is not initialized. Call initialize() first.")
        return self._model  # type: ignore

    def get_last_mesh(self) -> Optional[MeshData]:
        """Internal accessor for the most recently generated mesh."""
        return self._last_mesh

    def generate_baseline(
        self,
        presentation: Union[PresentationGender, str],
        stature_m: float = 1.5683,
    ) -> MeshData:
        """
        Generates an unedited neutral baseline mesh for a given presentation.
        All regional scales are neutral (0.0).
        """
        if not self.is_ready():
            raise EngineNotReadyError("Engine must be initialized before generating baseline.")

        # Convert presentation string to PresentationGender if needed
        if isinstance(presentation, str):
            pres_str = presentation.lower()
            if pres_str == "masculine":
                pres_enum = PresentationGender.MASCULINE
            elif pres_str == "feminine":
                pres_enum = PresentationGender.FEMININE
            elif pres_str == "neutral":
                pres_enum = PresentationGender.NEUTRAL
            else:
                raise InvalidParameterError(f"Invalid presentation: '{presentation}'.")
        else:
            pres_enum = presentation

        stature_cm = float(stature_m * 100.0)

        # Construct a neutral spec
        spec = AvatarShapeSpec(
            spec_version="1.2.1",
            presentation=pres_enum,
            target_stature_cm=stature_cm,
            target_measurements={"stature": stature_cm},
            regional_scales={
                reg: RegionalShapeScale(scale_x=0.0, scale_y=0.0, scale_z=0.0)
                for reg in ALL_ANATOMICAL_REGIONS
            },
            semantic_controls={},
        )
        return self.generate_avatar(spec)

    def generate_avatar(self, shape_spec: AvatarShapeSpec) -> MeshData:
        """
        Translates engine-independent AvatarShapeSpec into Anny parameters and performs
        PyTorch CPU forward inference, producing a verified MeshData entity.
        """
        if not self.is_ready():
            raise EngineNotReadyError("Engine must be initialized before generating avatar.")

        t_start = time.perf_counter()

        # 1. Validate presentation
        pres = shape_spec.presentation
        pres_str = pres.value if isinstance(pres, PresentationGender) else str(pres).lower()
        if pres_str == "masculine":
            gender_val = 1.0
        elif pres_str == "feminine":
            gender_val = 0.0
        elif pres_str == "neutral":
            gender_val = 0.5
        else:
            raise InvalidParameterError(f"Unsupported presentation '{pres}'.")

        # 2. Validate stature
        stature_cm = float(shape_spec.target_stature_cm)
        if math.isnan(stature_cm) or math.isinf(stature_cm) or not (100.0 <= stature_cm <= 230.0):
            raise InvalidParameterError(
                f"target_stature_cm must be in [100.0, 230.0] cm, got {stature_cm}"
            )

        # 3. Map phenotypes
        # In Anny, height parameter [0.0, 1.0] corresponds approximately to [105.0, 207.0] cm
        h_norm = (stature_cm - 105.0) / (207.0 - 105.0)
        h_clamped = float(np.clip(h_norm, 0.0, 1.0))

        phenotype_dict: Dict[str, float] = {
            "gender": gender_val,
            "age": 0.50,
            "muscle": 0.50,
            "weight": 0.50,
            "height": h_clamped,
            "proportions": 0.50,
        }

        # 4. Translate regional_scales to Anny local_changes_kwargs
        clamped_params: Dict[str, Tuple[float, float]] = {}
        local_kwargs: Dict[str, float] = {}

        reg_scales = shape_spec.regional_scales or {}

        def apply_local(param_name: str, requested_val: float, bound_min: float = -1.0, bound_max: float = 1.0) -> None:
            if math.isnan(requested_val) or math.isinf(requested_val):
                raise InvalidParameterError(f"Parameter '{param_name}' is non-finite ({requested_val}).")
            clamped = float(np.clip(requested_val, bound_min, bound_max))
            if abs(clamped - requested_val) > 1e-5:
                clamped_params[param_name] = (requested_val, clamped)
            local_kwargs[param_name] = clamped

        # Shoulders (scale_x: lateral width, scale_y: depth/muscle)
        if "shoulders" in reg_scales:
            sh = reg_scales["shoulders"]
            apply_local("measure-shoulder-dist-incr", sh.scale_x)
            apply_local("l-upperarm-shoulder-muscle-incr", sh.scale_y * 0.5)
            apply_local("r-upperarm-shoulder-muscle-incr", sh.scale_y * 0.5)

        # Chest (scale_y: pectoral / bust projection)
        if "torso_chest" in reg_scales:
            tc = reg_scales["torso_chest"]
            if pres_str == "feminine":
                apply_local("breast-volume-vert-up", tc.scale_y)
            elif pres_str == "masculine":
                apply_local("measure-frontchest-dist-incr", tc.scale_y)
            else:  # neutral
                apply_local("measure-frontchest-dist-incr", tc.scale_y * 0.5)
                apply_local("breast-volume-vert-up", tc.scale_y * 0.5)

        # Waist / Abdomen (scale_y: belly protrusion, scale_x: waist definition / indentation)
        if "waist_abdomen" in reg_scales:
            wa = reg_scales["waist_abdomen"]
            # Belly fullness (sagittal protrusion)
            apply_local("stomach-pregnant-incr", wa.scale_y)
            # Waist definition: scale_x is negative for narrow waist, positive for thick waist
            apply_local("measure-waist-circ-incr", wa.scale_x)

        # Arms (scale_x: lateral girth)
        if "arms" in reg_scales:
            ar = reg_scales["arms"]
            apply_local("l-upperarm-scale-horiz-incr", ar.scale_x)
            apply_local("r-upperarm-scale-horiz-incr", ar.scale_x)

        # Hips (scale_x: pelvic breadth / circumference)
        if "hips" in reg_scales:
            hp = reg_scales["hips"]
            apply_local("measure-hips-circ-incr", hp.scale_x)
            apply_local("hip-trans-out", hp.scale_x * 0.3)

        # Thighs (scale_x: upper leg girth)
        if "thighs" in reg_scales:
            th = reg_scales["thighs"]
            apply_local("measure-thigh-circ-incr", th.scale_x)
            apply_local("l-upperleg-fat-incr", th.scale_x * 0.5)
            apply_local("r-upperleg-fat-incr", th.scale_x * 0.5)

        # Calves (scale_x: lower leg gastrocnemius girth)
        if "calves" in reg_scales:
            cl = reg_scales["calves"]
            apply_local("measure-calf-circ-incr", cl.scale_x)
            apply_local("l-lowerleg-scale-horiz-incr", cl.scale_x * 0.5)
            apply_local("r-lowerleg-scale-horiz-incr", cl.scale_x * 0.5)

        # 5. Forward Pass (PyTorch CPU, no gradients)
        model = self.get_model()
        with torch.no_grad():
            out = model(
                pose_parameters=self._pose_params,
                phenotype_kwargs=phenotype_dict,
                local_changes_kwargs=local_kwargs,
            )

        verts_tensor = out.get("vertices", out.get("rest_vertices"))
        if verts_tensor is None:
            raise MeshDeformationError("Anny model output missing vertex tensors.")

        # Squeeze batch dimension if present
        verts_np = (
            verts_tensor[0].detach().cpu().numpy().astype(np.float32)
            if verts_tensor.dim() == 3
            else verts_tensor.detach().cpu().numpy().astype(np.float32)
        )

        # 6. Post-inference Exact Stature Alignment (Isotropic Scaling)
        # Anny height phenotype provides non-linear biomechanical scaling;
        # isotropic scaling guarantees exact millimeter matching to target_stature_cm.
        z_span = float(verts_np[:, 2].max() - verts_np[:, 2].min())
        target_m = stature_cm / 100.0
        if z_span > 0.01:
            scale_factor = target_m / z_span
            verts_np = (verts_np * scale_factor).astype(np.float32)

        # 7. Structural integrity validation
        if not np.isfinite(verts_np).all() or np.isnan(verts_np).any():
            raise MeshDeformationError("Forward pass produced non-finite or NaN vertex coordinates.")

        # Compute vertex normals
        faces = self._faces.copy() if self._faces is not None else np.zeros((0, 3), dtype=np.int32)
        tm = trimesh.Trimesh(vertices=verts_np, faces=faces, process=False)
        normals = np.asarray(tm.vertex_normals, dtype=np.float32)

        infer_time_ms = (time.perf_counter() - t_start) * 1000.0

        metadata = {
            "engine_name": "NAVER Anny",
            "engine_version": "0.6.2",
            "topology_identifier": "anny_v0.6.2_27420f",
            "presentation": pres_str,
            "target_stature_cm": stature_cm,
            "achieved_stature_cm": float((verts_np[:, 2].max() - verts_np[:, 2].min()) * 100.0),
            "vertex_count": int(verts_np.shape[0]),
            "face_count": int(faces.shape[0]),
            "clamped_parameters": clamped_params,
            "inference_time_ms": infer_time_ms,
        }

        mesh_data = MeshData(
            vertices=verts_np,
            faces=faces,
            normals=normals,
            metadata=metadata,
        )
        self._last_mesh = mesh_data
        return mesh_data

    def validate_mesh(self, mesh_data: MeshData) -> MeshValidationReport:
        """Performs topological, manifold, non-empty, and bounding box checks."""
        v = mesh_data.vertices
        f = mesh_data.faces

        has_nans = bool(np.isnan(v).any())
        has_infs = bool(np.isinf(v).any())

        bbox_min = (float(v[:, 0].min()), float(v[:, 1].min()), float(v[:, 2].min()))
        bbox_max = (float(v[:, 0].max()), float(v[:, 1].max()), float(v[:, 2].max()))

        tm = trimesh.Trimesh(vertices=v, faces=f, process=False)
        has_degenerate = bool(np.any(tm.area_faces <= 0.0))
        is_watertight = bool(tm.is_watertight)

        is_valid = (
            not has_nans
            and not has_infs
            and not has_degenerate
            and len(v) >= 3
            and len(f) >= 1
        )

        error_msg = None
        if not is_valid:
            errors = []
            if has_nans:
                errors.append("contains NaNs")
            if has_infs:
                errors.append("contains Infs")
            if has_degenerate:
                errors.append("contains degenerate zero-area faces")
            error_msg = "; ".join(errors)

        return MeshValidationReport(
            is_valid=is_valid,
            is_watertight=is_watertight,
            vertex_count=int(v.shape[0]),
            face_count=int(f.shape[0]),
            has_nans=has_nans,
            has_infs=has_infs,
            has_degenerate_faces=has_degenerate,
            bounding_box_min_m=bbox_min,
            bounding_box_max_m=bbox_max,
            error_message=error_msg,
        )

    def export_glb(self, mesh_data: MeshData) -> bytes:
        """
        Serializes MeshData to web-optimized glTF 2.0 binary container in memory.
        Applies canonical Z-up to Y-up axis conversion (R_x(-90°)) so the exported
        GLB model conforms strictly to glTF 2.0 / Three.js Y-up, +Z-forward conventions.
        Returns raw bytes directly; does not mutate source mesh_data.
        """
        try:
            # Canonical glTF 2.0 conversion matrix: R_x(-90°)
            # x_gltf = x_anny
            # y_gltf = z_anny (Head is +Y)
            # z_gltf = -y_anny (Front is +Z, facing viewer)
            # Determinant = +1.0 (pure rotation, preserves winding order and normals)
            t_rot_x_neg90 = np.array([
                [1.0,  0.0,  0.0, 0.0],
                [0.0,  0.0,  1.0, 0.0],
                [0.0, -1.0,  0.0, 0.0],
                [0.0,  0.0,  0.0, 1.0],
            ], dtype=np.float64)

            tm = trimesh.Trimesh(
                vertices=mesh_data.vertices.copy(),
                faces=mesh_data.faces.copy(),
                vertex_normals=mesh_data.normals.copy() if mesh_data.normals is not None else None,
                process=False,
            )
            tm.apply_transform(t_rot_x_neg90)

            glb_bytes = tm.export(file_type="glb")
            if not isinstance(glb_bytes, bytes):
                raise GLBExportError("Trimesh glb export did not return bytes.")
            return glb_bytes
        except Exception as e:
            raise GLBExportError(f"Failed to serialize mesh to GLB: {str(e)}") from e

    def get_landmark_provider(self, mesh: Optional[MeshData] = None) -> LandmarkProvider:
        """Returns landmark query interface for Anthropometry Engine, optionally bound to a specific mesh."""
        if mesh is not None:
            return AnnyLandmarkProvider(self, mesh=mesh)
        if self._landmark_provider is None:
            self._landmark_provider = AnnyLandmarkProvider(self)
        return self._landmark_provider

    def get_shape_evaluation_port(self) -> ShapeEvaluationPort:
        """Returns shape evaluation interface for BICE regularized solver."""
        if self._shape_evaluation_port is None:
            self._shape_evaluation_port = AnnyShapeEvaluationPort(self)
        return self._shape_evaluation_port

    def get_metadata(self) -> EngineMetadata:
        """Returns engine identity and hardware capabilities."""
        return EngineMetadata(
            engine_name="NAVER Anny",
            engine_version="0.6.2",
            topology_identifier="anny_v0.6.2_27420f",
            supports_lbs=True,
            supported_capabilities=[
                "mesh_generation",
                "glb_export",
                "shape_evaluation",
                "landmark_provider",
            ],
            device_type=self.device,
        )
