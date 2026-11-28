"""
WearWise Digital Garment Platform — Automated Quality Assurance & Confidence Engine
==================================================================================
Performs genuine, independent multi-vector QA on pattern-authored digital garments:
1. Pattern & Seam Integrity QA (7 required panels with 2D outlines, 1-to-1 ordinary
   seam-edge pairings, and explicit surface attachment path validation)
2. Geometry & Topology QA (degenerate triangles, non-manifold edges/vertices, Euler -2,
   4 expected garment openings vs unexpected holes, non-adjacent self-intersections)
3. Dimensional QA (explicit measurement definitions & tolerances; 2D flat pattern,
   3D assembled geometry, and avatar fit clearance strictly separated)
4. Material & UV QA (PBR metallic/roughness bounds, embedded texture >= 1024x1024, UV [0, 1])
5. Explicit Status Semantics (prototype QA statuses never masquerade as published SKUs)
"""

import os
import io
import logging
from collections import defaultdict
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

import numpy as np
import trimesh
import pygltflib
from PIL import Image
from scipy.spatial import cKDTree
from scipy.interpolate import LinearNDInterpolator

logger = logging.getLogger("wearwise.garment_platform.qa")

REQUIRED_COMPONENTS = [
    "PANEL-FRONT-TORSO",
    "PANEL-BACK-TORSO",
    "PANEL-SLEEVE-L",
    "PANEL-SLEEVE-R",
    "PANEL-COLLAR-RIB",
    "PANEL-HEM-BAND",
    "PANEL-POCKET-CHEST",
]

STRUCTURAL_SHELL_COMPONENTS = [
    "PANEL-FRONT-TORSO",
    "PANEL-BACK-TORSO",
    "PANEL-SLEEVE-L",
    "PANEL-SLEEVE-R",
    "PANEL-COLLAR-RIB",
    "PANEL-HEM-BAND",
]

# Explicit, justified dimensional tolerance contract (ISO 8559-2 / BS 4952 aligned)
DIMENSIONAL_TOLERANCE_CONTRACT = {
    "2d_pattern_cm": {
        "flat_half_chest_width_cm": {"tolerance_cm": 0.25, "definition": "2D front/back torso panel width between underarm seam points"},
        "back_length_hps_to_hem_cm": {"tolerance_cm": 0.25, "definition": "2D back panel HPS-to-hem-seam height + 2.8 cm hem band height"},
        "shoulder_breadth_cm": {"tolerance_cm": 0.25, "definition": "2D across-shoulder span between left and right dropped shoulder points"},
        "sleeve_centerline_length_cm": {"tolerance_cm": 0.25, "definition": "2D sleeve centerline height from cuff opening midpoint to cap apex"},
        "finished_collar_opening_circumference_cm": {"tolerance_cm": 0.25, "definition": "2D collar band top opening edge length (distinct from collar-to-body seam)"},
        "flat_bottom_hem_width_cm": {"tolerance_cm": 0.25, "definition": "2D hem band flat width (0.5 x total hem circumference)"},
        "flat_sleeve_opening_width_cm": {"tolerance_cm": 0.25, "definition": "2D sleeve cuff opening flat width (0.5 x cuff circumference)"},
    },
    "3d_assembled_cm": {
        "torso_chest_circumference_cm": {"tolerance_cm": 1.50, "definition": "Closed horizontal torso cross-section perimeter at y = underarm - 1.5 cm (excludes sleeves)"},
        "back_length_hps_to_hem_cm": {"tolerance_cm": 1.00, "definition": "Vertical span from back torso HPS (y_max) to bottom hem band opening (y_min)"},
        "shoulder_breadth_seam_to_seam_cm": {"tolerance_cm": 1.00, "definition": "Span across back between left and right dropped shoulder-armhole junctions"},
        "sleeve_centerline_length_cm": {"tolerance_cm": 1.00, "definition": "3D centerline Euclidean span from armhole cap midpoint to distal cuff opening centroid along A-pose arm axis (separate from 10.36 cm tapered underarm edge)"},
        "collar_opening_circumference_cm": {"tolerance_cm": 0.75, "definition": "Perimeter of finished top Neckline Opening boundary loop (distinct from 51.14 cm collar seam loop)"},
        "bottom_hem_perimeter_cm": {"tolerance_cm": 1.50, "definition": "Perimeter of Bottom Hem Opening boundary loop (compared to 2 x flat hem width)"},
        "sleeve_cuff_circumference_cm": {"tolerance_cm": 1.00, "definition": "Perimeter of Left/Right Sleeve Cuff Opening boundary loop (compared to 2 x flat cuff opening)"},
    },
}


def _to_serializable(val: Any) -> Any:
    """Recursively converts numpy types to standard Python primitives for BSON/JSON."""
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.floating, float)):
        return float(val)
    if isinstance(val, np.ndarray):
        return val.tolist()
    if isinstance(val, dict):
        return {k: _to_serializable(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_to_serializable(v) for v in val]
    return val


def _seg_tri_intersect(p0: np.ndarray, p1: np.ndarray, v0: np.ndarray, v1: np.ndarray, v2: np.ndarray) -> bool:
    d = p1 - p0
    e1 = v1 - v0
    e2 = v2 - v0
    n = np.cross(e1, e2)
    denom = float(np.dot(n, d))
    if abs(denom) < 1e-12:
        return False
    t = float(np.dot(n, v0 - p0)) / denom
    if t < 1e-6 or t > 1.0 - 1e-6:
        return False
    p = p0 + t * d
    vp = p - v0
    d00 = float(np.dot(e1, e1))
    d01 = float(np.dot(e1, e2))
    d11 = float(np.dot(e2, e2))
    d20 = float(np.dot(vp, e1))
    d21 = float(np.dot(vp, e2))
    inv_denom = d00 * d11 - d01 * d01
    if abs(inv_denom) < 1e-18:
        return False
    u = (d11 * d20 - d01 * d21) / inv_denom
    v = (d00 * d21 - d01 * d20) / inv_denom
    return (u >= -1e-6) and (v >= -1e-6) and (u + v <= 1.0 + 1e-6)


def _tri_tri_intersect(t1: np.ndarray, t2: np.ndarray) -> bool:
    for a, b in [(0, 1), (1, 2), (2, 0)]:
        if _seg_tri_intersect(t1[a], t1[b], t2[0], t2[1], t2[2]):
            return True
        if _seg_tri_intersect(t2[a], t2[b], t1[0], t1[1], t1[2]):
            return True
    return False


def _slice_closed_loops_at_y(mesh: trimesh.Trimesh, y_height: float) -> List[Dict[str, Any]]:
    lines = trimesh.intersections.mesh_plane(mesh, plane_normal=[0, 1, 0], plane_origin=[0, y_height, 0])
    if len(lines) == 0:
        return []
    seg_lens = np.linalg.norm(lines[:, 1] - lines[:, 0], axis=1)
    adj = defaultdict(list)

    def _k(pt: np.ndarray):
        return (round(float(pt[0]), 4), round(float(pt[1]), 4), round(float(pt[2]), 4))

    for idx, (a, b) in enumerate(lines):
        ka, kb = _k(a), _k(b)
        adj[ka].append((kb, idx))
        adj[kb].append((ka, idx))

    visited = set()
    comps = []
    for idx, (a, b) in enumerate(lines):
        if idx in visited:
            continue
        q = [_k(a), _k(b)]
        seen = set(q)
        c_segs, c_pts = [], []
        while q:
            ck = q.pop()
            for nk, sidx in adj[ck]:
                if sidx not in visited:
                    visited.add(sidx)
                    c_segs.append(sidx)
                    c_pts.extend(lines[sidx])
                if nk not in seen:
                    seen.add(nk)
                    q.append(nk)
        arr = np.array(c_pts)
        comps.append({
            "perimeter_cm": round(float(seg_lens[c_segs].sum()) * 100.0, 2),
            "x_span_cm": round(float(arr[:, 0].max() - arr[:, 0].min()) * 100.0, 2),
            "z_span_cm": round(float(arr[:, 2].max() - arr[:, 2].min()) * 100.0, 2),
            "centroid_x": round(float(arr[:, 0].mean()), 4),
        })
    comps.sort(key=lambda c: c["perimeter_cm"], reverse=True)
    return comps


class GarmentQAEngine:
    """Automated Quality Assurance inspector for pattern-authored digital garment packages."""

    @classmethod
    def evaluate_prototype_glb(
        cls,
        glb_path: str,
        target_measurements: Dict[str, Any],
        size_label: str = "M",
        panel_metadata: Optional[List[Dict[str, Any]]] = None,
        seam_map: Optional[List[Dict[str, Any]]] = None,
        surface_attachments: Optional[List[Dict[str, Any]]] = None,
        avatar_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full independent engineering QA of a prototype GLB.
        Explicitly separates prototype QA statuses from publication status.
        """
        issues: List[str] = []

        if not os.path.exists(glb_path):
            return _to_serializable({
                "statuses": {
                    "prototype_geometry_qa": "FAILED",
                    "pattern_seam_qa": "FAILED",
                    "material_uv_qa": "FAILED",
                    "dimensional_qa": "FAILED",
                    "overall_prototype_qa": "FAILED",
                    "publication_status": "NOT_PUBLISHED_PROTOTYPE_ONLY",
                },
                "qa_gate": {"passed": False, "blocking_issues": [f"GLB missing: {glb_path}"]},
            })

        # 1. Pattern, 2D outline, seam-edge, and attachment path QA
        pattern_qa = cls._inspect_pattern_and_seams(
            panel_metadata=panel_metadata,
            seam_map=seam_map,
            surface_attachments=surface_attachments,
            target_measurements=target_measurements,
        )
        if not pattern_qa["passed"]:
            issues.extend(pattern_qa.get("errors", []))

        # 2. 3D Geometry & Topology QA (garment-only)
        geom_qa = cls._inspect_mesh_geometry(glb_path, size_label)
        if not geom_qa.get("passed"):
            issues.extend(geom_qa.get("errors", [geom_qa.get("error", "Geometry QA failed")]))

        # 3. Material & UV Integrity QA
        mat_uv_qa = cls._inspect_material_and_uv(glb_path)
        if not mat_uv_qa.get("passed"):
            issues.extend(mat_uv_qa.get("errors", ["Material/UV QA failed"]))

        # 4. Dimensional QA (2D pattern vs 3D assembled reported separately with explicit tolerances)
        meas_qa = cls._inspect_mesh_measurements(
            glb_path=glb_path,
            geom_check=geom_qa,
            spec=target_measurements,
            size_label=size_label,
        )
        if not meas_qa.get("passed"):
            issues.extend(meas_qa.get("errors", ["Dimensional QA failed"]))

        # 5. Isolated Avatar Fit Reference & Full-3D Clearance QA (never conflated with garment geometry metrics)
        avatar_metrics = None
        fit_qa_passed = True
        if avatar_path and os.path.exists(avatar_path):
            avatar_metrics = cls._inspect_avatar_fit_clearance(glb_path, avatar_path)
            fit_qa_passed = bool(avatar_metrics.get("fit_clearance_passed", True))
            if not fit_qa_passed:
                issues.extend(avatar_metrics.get("fit_clearance_errors", ["Full-3D avatar fit clearance check failed"]))

        overall_passed = len(issues) == 0
        return _to_serializable({
            "sku": "TSH-WW-CREW-001",
            "size_label": size_label,
            "glb_path": glb_path,
            "statuses": {
                "prototype_geometry_qa": "PASSED" if geom_qa.get("passed") else "FAILED",
                "pattern_seam_qa": "PASSED" if pattern_qa.get("passed") else "FAILED",
                "material_uv_qa": "PASSED" if mat_uv_qa.get("passed") else "FAILED",
                "dimensional_qa": "PASSED" if meas_qa.get("passed") else "FAILED",
                "fit_clearance_qa": ("PASSED" if fit_qa_passed else "FAILED") if avatar_metrics else "SKIPPED_NO_AVATAR",
                "overall_prototype_qa": "PASSED" if overall_passed else "FAILED",
                "publication_status": "NOT_PUBLISHED_PROTOTYPE_ONLY",
            },
            "tolerance_contract": DIMENSIONAL_TOLERANCE_CONTRACT,
            "checks": {
                "pattern_seam_qa": pattern_qa,
                "geometry_topology_qa": geom_qa,
                "material_uv_qa": mat_uv_qa,
                "dimensional_qa": meas_qa,
            },
            "avatar_fit_reference": avatar_metrics,
            "qa_gate": {
                "passed": overall_passed,
                "blocking_issues": issues,
                "note": "Prototype QA gate only; does not indicate published catalog status.",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    @classmethod
    def run_full_qa(
        cls,
        garment_doc: Dict[str, Any],
        generated_meshes: Optional[Dict[str, Any]] = None,
        fabric_profile: Optional[Dict[str, Any]] = None,
        pattern_data: Optional[Dict[str, Any]] = None,
        measurements: Optional[Dict[str, Any]] = None,
        garment_dir: Optional[str] = None,
        avatar_path: Optional[str] = None,
        glb_paths_by_size: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        if not garment_dir:
            garment_dir = os.path.join(os.getcwd(), "..", "frontend", "public", "garments")
            if not os.path.exists(garment_dir):
                garment_dir = os.path.join(os.getcwd(), "artifacts", "garments")

        doc_copy = dict(garment_doc)
        if pattern_data:
            doc_copy["pattern"] = pattern_data
        if measurements:
            doc_copy["measurements"] = measurements

        raw_report = cls.evaluate_garment(
            doc_copy,
            garment_dir,
            avatar_path,
            glb_paths_by_size=glb_paths_by_size,
        )
        checks = {
            "geometry_qa": {
                "status": "PASSED" if raw_report.get("geometry_qa") and all(g.get("passed", False) for g in raw_report.get("geometry_qa", {}).values()) else "FAILED",
                "details": raw_report.get("geometry_qa"),
            },
            "measurement_qa": {
                "status": "PASSED" if raw_report.get("measurement_qa") and all(m.get("passed", False) for m in raw_report.get("measurement_qa", {}).values()) else "FAILED",
                "details": raw_report.get("measurement_qa"),
            },
            "material_uv_qa": {
                "status": "PASSED" if raw_report.get("material_uv_qa") and all(m.get("passed", False) for m in raw_report.get("material_uv_qa", {}).values()) else "FAILED",
                "details": raw_report.get("material_uv_qa"),
            },
            "fit_clearance_qa": {
                "status": "PASSED" if raw_report.get("fit_clearance_qa") and all(f.get("fit_clearance_passed", False) for f in raw_report.get("fit_clearance_qa", {}).values()) else "FAILED",
                "details": raw_report.get("fit_clearance_qa"),
            },
            "texture_qa": {
                "status": "PASSED" if raw_report.get("texture_qa", {}).get("passed", False) else "FAILED",
                "details": raw_report.get("texture_qa"),
            },
            "variant_qa": {
                "status": "PASSED" if raw_report.get("variant_qa", {}).get("distinct_geometries", False) else "FAILED",
                "details": raw_report.get("variant_qa"),
            },
        }
        return _to_serializable({
            "sku": garment_doc.get("sku", "TSH-WW-CREW-001"),
            "overall_status": raw_report.get("overall_status", "FAILED"),
            "confidence_level": raw_report.get("confidence_level", "PARAMETRIC_TEMPLATE"),
            "checks": checks,
            "publication_gate": raw_report.get("publication_gate", {"passed": False}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": (
                f"Automated QA: Geometry ({checks['geometry_qa']['status']}), "
                f"Measurements ({checks['measurement_qa']['status']}), "
                f"Material/UV ({checks['material_uv_qa']['status']}), "
                f"Fit ({checks['fit_clearance_qa']['status']}), "
                f"Variants ({checks['variant_qa']['status']})."
            ),
        })

    @classmethod
    def evaluate_garment(
        cls,
        garment_doc: Dict[str, Any],
        garment_dir: str,
        avatar_path: Optional[str] = None,
        glb_paths_by_size: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        sku = garment_doc.get("sku", "UNKNOWN")
        pattern = garment_doc.get("pattern", {})
        measurements = garment_doc.get("measurements", {})

        qa_report = {
            "sku": sku,
            "overall_status": "PASSED",
            "confidence_level": cls._determine_confidence_level(pattern),
            "geometry_qa": {},
            "measurement_qa": {},
            "material_uv_qa": {},
            "fit_clearance_qa": {},
            "texture_qa": {},
            "variant_qa": {},
            "publication_gate": {"passed": True, "blocking_issues": []},
        }

        available_sizes = garment_doc.get("available_sizes", ["S", "M", "L"])
        variant_details = {}

        for sz in available_sizes:
            glb_path = (glb_paths_by_size or {}).get(sz) or os.path.join(garment_dir, f"{sku}_{sz}.glb")
            glb_filename = os.path.basename(glb_path)
            if not os.path.exists(glb_path):
                qa_report["publication_gate"]["blocking_issues"].append(f"Missing 3D GLB for Size {sz} ({glb_filename})")
                continue

            geom_check = cls._inspect_mesh_geometry(glb_path, sz)
            qa_report["geometry_qa"][sz] = geom_check
            if not geom_check["passed"]:
                qa_report["publication_gate"]["blocking_issues"].append(
                    f"Size {sz} failed geometry QA: {'; '.join(geom_check.get('errors', []))}"
                )

            spec = measurements.get(sz, {})
            meas_check = cls._inspect_mesh_measurements(glb_path, geom_check, spec, sz)
            qa_report["measurement_qa"][sz] = meas_check
            if not meas_check["passed"]:
                qa_report["publication_gate"]["blocking_issues"].append(
                    f"Size {sz} failed measurement QA: {'; '.join(meas_check.get('errors', []))}"
                )

            mat_check = cls._inspect_material_and_uv(glb_path)
            qa_report["material_uv_qa"][sz] = mat_check
            if not mat_check.get("passed"):
                qa_report["publication_gate"]["blocking_issues"].append(
                    f"Size {sz} failed material/UV QA: {'; '.join(mat_check.get('errors', []))}"
                )

            fit_check = cls._inspect_avatar_fit_clearance(glb_path, avatar_path)
            qa_report["fit_clearance_qa"][sz] = fit_check
            if not fit_check.get("fit_clearance_passed"):
                qa_report["publication_gate"]["blocking_issues"].append(
                    f"Size {sz} failed baseline A-pose fit clearance QA: {'; '.join(fit_check.get('fit_clearance_errors', []))}"
                )

            variant_details[sz] = {
                "glb_file": glb_filename,
                "vertices": geom_check.get("garment_vertex_count"),
                "faces": geom_check.get("garment_face_count"),
                "component_count": geom_check.get("component_count"),
                "euler_characteristic": geom_check.get("euler_characteristic"),
                "bounds_min_m": geom_check.get("bounds_min_m"),
                "bounds_max_m": geom_check.get("bounds_max_m"),
            }

        if len(variant_details) >= 2:
            sigs = {
                (
                    d["vertices"],
                    d["faces"],
                    tuple(d.get("bounds_min_m") or ()),
                    tuple(d.get("bounds_max_m") or ()),
                )
                for d in variant_details.values()
            }
            distinct = len(sigs) == len(variant_details)
            qa_report["variant_qa"] = {
                "distinct_geometries": distinct,
                "size_variants": variant_details,
            }
        else:
            qa_report["variant_qa"] = {"distinct_geometries": len(variant_details) == 1, "size_variants": variant_details}

        atlas_candidates = [
            os.path.join(garment_dir, "garment_texture_diffuse.png"),
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "frontend", "public", "garments", "garment_texture_diffuse.png"),
            os.path.join(os.getcwd(), "artifacts", "garments", "garment_texture_diffuse.png"),
        ]
        atlas_path = next((p for p in atlas_candidates if os.path.exists(p)), atlas_candidates[0])
        texture_check = cls._inspect_texture_atlas(atlas_path)
        qa_report["texture_qa"] = texture_check
        if not texture_check["passed"]:
            qa_report["publication_gate"]["blocking_issues"].append(f"Texture QA failed: {texture_check.get('error')}")

        has_blocking = len(qa_report["publication_gate"]["blocking_issues"]) > 0
        qa_report["publication_gate"]["passed"] = not has_blocking
        qa_report["overall_status"] = "PASSED" if not has_blocking else "FAILED"
        return qa_report

    @classmethod
    def _determine_confidence_level(cls, pattern: Dict[str, Any]) -> str:
        mode = pattern.get("pattern_mode", "parametric")
        if mode in ["cad_dxf", "svg"] and pattern.get("has_cad_data"):
            return "VERIFIED_PATTERN"
        if mode in ["ai_reconstruct", "ai_reconstructed"]:
            return "AI_RECONSTRUCTED"
        return "PARAMETRIC_TEMPLATE"

    @classmethod
    def _inspect_pattern_and_seams(
        cls,
        panel_metadata: Optional[List[Dict[str, Any]]],
        seam_map: Optional[List[Dict[str, Any]]],
        surface_attachments: Optional[List[Dict[str, Any]]],
        target_measurements: Dict[str, Any],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not panel_metadata:
            return {"passed": False, "errors": ["Missing 2D pattern component metadata"]}
        if not seam_map:
            return {"passed": False, "errors": ["Missing explicit seam-edge map"]}

        panels_by_id = {p.get("panel_id"): p for p in panel_metadata}
        missing = [req for req in REQUIRED_COMPONENTS if req not in panels_by_id]
        if missing:
            errors.append(f"Missing declared pattern panels: {missing}")

        # Verify every panel has 2D outline coordinates and outline edge lengths match edge records
        outline_checks = {}
        for pid, p in panels_by_id.items():
            outline = p.get("outline_2d_cm")
            edges = p.get("edges", {})
            if not outline or len(outline) < 3:
                errors.append(f"Panel {pid} lacks inspectable 2D outline coordinates.")
                continue
            for eid, edata in edges.items():
                coords = np.array(edata.get("coordinates_cm", []), dtype=np.float64)
                if len(coords) < 2:
                    errors.append(f"Edge {pid}:{eid} lacks 2D coordinates.")
                    continue
                calc_len = round(float(np.linalg.norm(np.diff(coords, axis=0), axis=1).sum()), 2)
                rec_len = round(float(edata.get("length_cm", -1)), 2)
                if abs(calc_len - rec_len) > 0.05:
                    errors.append(f"Edge {pid}:{eid} length mismatch: outline={calc_len} cm vs recorded={rec_len} cm")
            outline_checks[pid] = {"outline_vertices": len(outline), "edges_verified": len(edges)}

        # Strictly verify every ordinary seam references real panel IDs and real edge IDs (no composite IDs!)
        incompat_seams = []
        for s in seam_map:
            sid = s.get("seam_id")
            if s.get("record_kind") != "ordinary_sewing_seam":
                errors.append(f"Seam {sid} has invalid record_kind '{s.get('record_kind')}' in ordinary seam list.")
                continue
            sp = s.get("source_panel_id")
            se = s.get("source_edge_id")
            dp = s.get("dest_panel_id")
            de = s.get("dest_edge_id")
            if sp not in panels_by_id:
                errors.append(f"Seam {sid} references unknown source_panel_id '{sp}'.")
            elif se not in panels_by_id[sp].get("edges", {}):
                errors.append(f"Seam {sid} references nonexistent source_edge_id '{se}' on '{sp}'.")

            if dp not in panels_by_id:
                errors.append(f"Seam {sid} references unknown dest_panel_id '{dp}'.")
            elif de not in panels_by_id[dp].get("edges", {}):
                errors.append(f"Seam {sid} references nonexistent dest_edge_id '{de}' on '{dp}'.")

            if not s.get("compatible", False):
                incompat_seams.append(sid)

            if sid == "SEAM-COLLAR-JOIN":
                tc = s.get("transformation_contract")
                if not tc or tc.get("cause") != "conical_ring_curvature_development":
                    errors.append("Seam SEAM-COLLAR-JOIN lacks valid 'conical_ring_curvature_development' transformation_contract.")
                else:
                    exp_2d = float(tc.get("expected_2d_stitch_slant_cm", -1.0))
                    exp_3d = float(tc.get("expected_3d_meridian_cm", -1.0))
                    tol_c = float(tc.get("tolerance_cm", 0.25))
                    act_2d_s = float(s.get("actual_2d_source_length_cm", -99.0))
                    act_3d_s = float(s.get("actual_3d_source_length_cm", -99.0))
                    if abs(act_2d_s - exp_2d) > tol_c:
                        errors.append(f"Collar closure 2D slant {act_2d_s} cm deviates from contract expected {exp_2d} cm (> {tol_c} cm).")
                    if abs(act_3d_s - exp_3d) > tol_c:
                        errors.append(f"Collar closure 3D meridian {act_3d_s} cm deviates from contract expected {exp_3d} cm (> {tol_c} cm).")
                    if abs(act_2d_s - act_3d_s) < 0.30:
                        errors.append("Collar closure 2D and 3D lengths appear artificially equalized despite ring taper.")

        if incompat_seams:
            errors.append(f"Incompatible seam edge pairings: {incompat_seams}")

        # Validate cut lines + seam allowances on each panel
        for pid, p in panels_by_id.items():
            if not p.get("cut_line_2d_cm"):
                errors.append(f"Panel {pid} lacks explicit outer seam-allowance cut_line_2d_cm contour.")

        # Validate surface attachment paths (e.g., chest pocket)
        if not surface_attachments:
            errors.append("Missing surface_attachments record (chest pocket attachment path).")
        else:
            for att in surface_attachments:
                aid = att.get("attachment_id")
                sp = att.get("source_panel_id")
                tp = att.get("target_panel_id")
                if sp not in panels_by_id or tp not in panels_by_id:
                    errors.append(f"Attachment {aid} references unknown panel(s): {sp} -> {tp}")
                    continue
                for eid in att.get("source_edge_ids", []):
                    if eid not in panels_by_id[sp].get("edges", {}):
                        errors.append(f"Attachment {aid} references unknown source edge '{eid}' on '{sp}'.")
                if att.get("target_attachment_type") != "interior_surface_path":
                    errors.append(f"Attachment {aid} must use target_attachment_type='interior_surface_path'.")
                if not att.get("target_surface_path_2d_cm") or not att.get("target_surface_path_3d_m"):
                    errors.append(f"Attachment {aid} lacks 2D/3D target surface path coordinates.")
                ac = att.get("attachment_contract")
                if not ac or ac.get("mapping_relationship") != "planar_chest_box_to_curved_3d_torso_surface_with_normal_relief":
                    errors.append(f"Attachment {aid} lacks explicit surface projection attachment_contract.")
                else:
                    exp_2d = float(att.get("expected_path_length_cm", -1.0))
                    act_2d = float(att.get("actual_2d_path_length_cm", -99.0))
                    exp_p3d = float(att.get("expected_projected_3d_path_length_cm", -1.0))
                    act_3d = float(att.get("actual_3d_path_length_cm", -99.0))
                    tols = ac.get("tolerances", {})
                    if abs(act_2d - exp_2d) > float(tols.get("tolerance_2d_cm", 0.25)):
                        errors.append(f"Attachment {aid} 2D path length {act_2d} vs expected {exp_2d} cm out of tolerance.")
                    if abs(act_3d - exp_p3d) > float(tols.get("tolerance_3d_projection_cm", 1.00)):
                        errors.append(f"Attachment {aid} 3D path length {act_3d} vs projected surface {exp_p3d} cm out of tolerance.")
                    relief = ac.get("measured_rim_relief_mm", {})
                    mean_rel = float(relief.get("mean", -1.0))
                    if abs(mean_rel - 3.5) > float(tols.get("relief_tolerance_mm", 1.0)) or float(relief.get("min", -1.0)) <= 0.0:
                        errors.append(f"Attachment {aid} relief {mean_rel:.2f} mm out of tolerance around 3.5 mm.")
                if not att.get("compatible", False):
                    errors.append(f"Attachment {aid} failed path compatibility check.")

        # Validate 2D pattern dimensions against explicit 2D tolerance contract
        tol_2d = DIMENSIONAL_TOLERANCE_CONTRACT["2d_pattern_cm"]
        d_f = panels_by_id.get("PANEL-FRONT-TORSO", {}).get("dimensions_2d_cm", {})
        d_b = panels_by_id.get("PANEL-BACK-TORSO", {}).get("dimensions_2d_cm", {})
        d_c = panels_by_id.get("PANEL-COLLAR-RIB", {}).get("dimensions_2d_cm", {})
        d_h = panels_by_id.get("PANEL-HEM-BAND", {}).get("dimensions_2d_cm", {})
        d_s = panels_by_id.get("PANEL-SLEEVE-L", {}).get("dimensions_2d_cm", {})

        pattern_checks = {
            "flat_half_chest_width_cm": (d_f.get("half_chest_width_cm"), float(target_measurements.get("half_chest_width_cm", 54.0))),
            "back_length_hps_to_hem_cm": (
                round(float(d_b.get("body_length_hps_to_hem_seam_cm", 0)) + float(d_h.get("band_height_cm", 0)), 2),
                float(target_measurements.get("back_length_cm", 67.0)),
            ),
            "shoulder_breadth_cm": (d_b.get("shoulder_breadth_cm"), float(target_measurements.get("shoulder_breadth_cm", 50.0))),
            "sleeve_centerline_length_cm": (d_s.get("sleeve_length_cm"), float(target_measurements.get("sleeve_length_cm", 17.0))),
            "finished_collar_opening_circumference_cm": (d_c.get("finished_collar_opening_circumference_cm"), float(target_measurements.get("collar_circumference_cm", 44.0))),
            "flat_bottom_hem_width_cm": (d_h.get("hem_flat_width_cm"), float(target_measurements.get("hem_width_cm", 53.0))),
            "flat_sleeve_opening_width_cm": (d_s.get("cuff_opening_flat_width_cm"), float(target_measurements.get("sleeve_opening_cm", 20.5))),
        }

        dim_2d_results = {}
        for name, (actual, target) in pattern_checks.items():
            tol = tol_2d[name]["tolerance_cm"]
            err_val = None if actual is None else round(abs(float(actual) - target), 3)
            passed_dim = (err_val is not None) and (err_val <= tol)
            if not passed_dim:
                errors.append(f"2D pattern dimension '{name}' out of tolerance: actual={actual}, target={target}, tol=+/-{tol}")
            dim_2d_results[name] = {
                "actual_cm": actual,
                "target_cm": target,
                "abs_error_cm": err_val,
                "tolerance_cm": tol,
                "passed": passed_dim,
            }

        return {
            "passed": len(errors) == 0,
            "panel_count": len(panel_metadata),
            "ordinary_seam_count": len(seam_map),
            "surface_attachment_count": len(surface_attachments or []),
            "incompatible_seams": incompat_seams,
            "outline_checks": outline_checks,
            "pattern_2d_dimension_checks": dim_2d_results,
            "errors": errors,
        }

    @classmethod
    def _inspect_mesh_geometry(cls, glb_path: str, size_label: str) -> Dict[str, Any]:
        errors: List[str] = []
        try:
            scene = trimesh.load(glb_path, force="scene", process=False)
            geoms = dict(scene.geometry)
            if not geoms:
                return {"passed": False, "errors": ["Empty GLB scene"]}

            missing_nodes = [c for c in REQUIRED_COMPONENTS if c not in geoms]
            if missing_nodes:
                errors.append(f"GLB missing required pattern components: {missing_nodes}")

            garment_verts = sum(len(m.vertices) for m in geoms.values())
            garment_faces = sum(len(m.faces) for m in geoms.values())

            shell_parts = [geoms[k] for k in STRUCTURAL_SHELL_COMPONENTS if k in geoms]
            if not shell_parts:
                shell_parts = list(geoms.values())
            comb_shell = trimesh.util.concatenate(shell_parts)
            welded = trimesh.Trimesh(vertices=comb_shell.vertices, faces=comb_shell.faces, process=True)

            if welded.is_watertight:
                errors.append("Garment shell is watertight; expected open neck, hem, and cuff boundaries.")

            all_comb = trimesh.util.concatenate(list(geoms.values()))
            all_welded = trimesh.Trimesh(vertices=all_comb.vertices, faces=all_comb.faces, process=True)
            degenerate_count = int(np.sum(all_welded.area_faces < 1e-10))
            if degenerate_count > 0:
                errors.append(f"Found {degenerate_count} degenerate zero-area triangles.")

            V = len(welded.vertices)
            E = len(welded.edges_unique)
            F = len(welded.faces)
            euler_char = V - E + F

            edges_sorted = welded.edges_sorted
            unique_edges, counts = np.unique(edges_sorted, axis=0, return_counts=True)
            boundary_edges = unique_edges[counts == 1]
            non_manifold_edges = int(np.sum(counts > 2))
            if non_manifold_edges > 0:
                errors.append(f"Found {non_manifold_edges} non-manifold edges on welded shell.")

            nm_verts = cls._count_non_manifold_vertices(welded)
            if nm_verts > 0:
                errors.append(f"Found {nm_verts} non-manifold vertices on welded shell.")

            shell_comps = trimesh.graph.connected_components(welded.face_adjacency, min_len=1)
            if len(shell_comps) != 1:
                errors.append(f"Structural garment shell has {len(shell_comps)} disconnected components (expected 1).")

            loops = cls._trace_boundary_loops(welded, boundary_edges)
            if len(loops) != 4:
                errors.append(f"Expected 4 garment opening loops (neck, hem, L/R cuffs), found {len(loops)}.")
            unexpected_loops = [lp for lp in loops if lp["classified_role"] == "UNEXPECTED_OPENING" or not lp["closed"]]
            if unexpected_loops:
                errors.append(f"Found unexpected holes or unclosed boundary fragments: {unexpected_loops}")

            if euler_char != -2:
                errors.append(f"Expected Euler characteristic -2 for 4-opening garment shell, got {euler_char}.")

            self_int_count = cls._count_self_intersections(all_welded)
            if self_int_count > 0:
                errors.append(f"Detected {self_int_count} non-adjacent self-intersecting triangle pairs.")

            bmin, bmax = all_welded.bounds[0], all_welded.bounds[1]
            return {
                "passed": len(errors) == 0,
                "errors": errors,
                "component_count": len(geoms),
                "component_names": list(geoms.keys()),
                "garment_vertex_count": int(garment_verts),
                "garment_face_count": int(garment_faces),
                "welded_shell_vertices": int(V),
                "welded_shell_edges": int(E),
                "welded_shell_faces": int(F),
                "euler_characteristic": int(euler_char),
                "is_non_watertight": not welded.is_watertight,
                "is_winding_consistent": bool(all_welded.is_winding_consistent),
                "degenerate_faces_count": degenerate_count,
                "non_manifold_edges_count": non_manifold_edges,
                "non_manifold_vertices_count": nm_verts,
                "shell_connected_components": len(shell_comps),
                "boundary_edges_count": int(len(boundary_edges)),
                "boundary_loops_count": len(loops),
                "boundary_loops": loops,
                "self_intersecting_triangle_pairs": self_int_count,
                "bounds_min_m": [round(float(x), 4) for x in bmin],
                "bounds_max_m": [round(float(x), 4) for x in bmax],
            }
        except Exception as err:
            return {"passed": False, "errors": [str(err)], "error": str(err)}

    @classmethod
    def _count_non_manifold_vertices(cls, mesh: trimesh.Trimesh) -> int:
        v_to_faces = defaultdict(list)
        for fi, face in enumerate(mesh.faces):
            for vi in face:
                v_to_faces[int(vi)].append(fi)
        nm_count = 0
        for vi, flist in v_to_faces.items():
            if len(flist) <= 1:
                continue
            f_adj = defaultdict(list)
            edge_map = defaultdict(list)
            for fi in flist:
                for ov in mesh.faces[fi]:
                    if int(ov) != vi:
                        edge_map[int(ov)].append(fi)
            bad = False
            for fl in edge_map.values():
                if len(fl) == 2:
                    f_adj[fl[0]].append(fl[1])
                    f_adj[fl[1]].append(fl[0])
                elif len(fl) > 2:
                    bad = True
                    break
            if bad:
                nm_count += 1
                continue
            seen = {flist[0]}
            q = [flist[0]]
            while q:
                c = q.pop()
                for nb in f_adj[c]:
                    if nb not in seen:
                        seen.add(nb)
                        q.append(nb)
            if len(seen) != len(flist):
                nm_count += 1
        return nm_count

    @classmethod
    def _trace_boundary_loops(cls, mesh: trimesh.Trimesh, boundary_edges: np.ndarray) -> List[Dict[str, Any]]:
        if len(boundary_edges) == 0:
            return []
        adj = defaultdict(list)
        for u, v in boundary_edges:
            u, v = int(u), int(v)
            adj[u].append(v)
            adj[v].append(u)

        visited_edges = set()
        loops = []
        for su in sorted(adj.keys()):
            for sv in adj[su]:
                ek = (min(su, sv), max(su, sv))
                if ek in visited_edges:
                    continue
                chain = [su, sv]
                visited_edges.add(ek)
                curr, prev = sv, su
                closed = False
                while True:
                    nbs = [n for n in adj[curr] if n != prev and (min(curr, n), max(curr, n)) not in visited_edges]
                    if not nbs:
                        if su in adj[curr] and len(chain) > 2:
                            closed = True
                        break
                    nxt = nbs[0]
                    visited_edges.add((min(curr, nxt), max(curr, nxt)))
                    if nxt == su:
                        closed = True
                        break
                    chain.append(nxt)
                    prev, curr = curr, nxt

                pts = mesh.vertices[chain]
                pts_c = np.vstack([pts, pts[0:1]]) if closed else pts
                perim_cm = float(np.linalg.norm(np.diff(pts_c, axis=0), axis=1).sum()) * 100.0
                cx, cy, cz = float(pts[:, 0].mean()), float(pts[:, 1].mean()), float(pts[:, 2].mean())
                if abs(cx) < 0.08 and cy > 1.25:
                    role = "Neckline Opening"
                elif abs(cx) < 0.08 and cy < 0.85:
                    role = "Bottom Hem Opening"
                elif cx > 0.22:
                    role = "Left Sleeve Cuff Opening"
                elif cx < -0.22:
                    role = "Right Sleeve Cuff Opening"
                else:
                    role = "UNEXPECTED_OPENING"

                loops.append({
                    "vertex_count": len(chain),
                    "closed": closed,
                    "perimeter_cm": round(perim_cm, 2),
                    "centroid_m": [round(cx, 4), round(cy, 4), round(cz, 4)],
                    "classified_role": role,
                })
        return loops

    @classmethod
    def _count_self_intersections(cls, mesh: trimesh.Trimesh) -> int:
        verts, faces = mesh.vertices, mesh.faces
        n_faces = len(faces)
        tris = verts[faces]
        tri_min = tris.min(axis=1) - 1e-6
        tri_max = tris.max(axis=1) + 1e-6
        count = 0
        chunk = 500
        for i0 in range(0, n_faces, chunk):
            i1 = min(i0 + chunk, n_faces)
            overlap = np.all(
                (tri_min[i0:i1, None, :] <= tri_max[None, :, :]) & (tri_max[i0:i1, None, :] >= tri_min[None, :, :]),
                axis=2,
            )
            rows, cols = np.where(overlap)
            for r, c in zip(rows, cols):
                fi, fj = i0 + int(r), int(c)
                if fj <= fi:
                    continue
                f_i, f_j = faces[fi], faces[fj]
                if (
                    f_i[0] == f_j[0] or f_i[0] == f_j[1] or f_i[0] == f_j[2]
                    or f_i[1] == f_j[0] or f_i[1] == f_j[1] or f_i[1] == f_j[2]
                    or f_i[2] == f_j[0] or f_i[2] == f_j[1] or f_i[2] == f_j[2]
                ):
                    continue
                if _tri_tri_intersect(tris[fi], tris[fj]):
                    count += 1
        return count

    @classmethod
    def _inspect_material_and_uv(cls, glb_path: str) -> Dict[str, Any]:
        errors: List[str] = []
        gltf = pygltflib.GLTF2().load(glb_path)
        if not gltf.materials:
            return {"passed": False, "errors": ["No PBR materials found in GLB"]}

        mats_summary = []
        for mat in gltf.materials:
            pbr = mat.pbrMetallicRoughness
            metallic = float(pbr.metallicFactor) if (pbr and pbr.metallicFactor is not None) else 1.0
            roughness = float(pbr.roughnessFactor) if (pbr and pbr.roughnessFactor is not None) else 1.0
            tex_idx = pbr.baseColorTexture.index if (pbr and pbr.baseColorTexture) else None
            if metallic > 0.20:
                errors.append(f"Material '{mat.name}' has non-textile metallicFactor={metallic:.2f} (> 0.20).")
            if roughness < 0.30 or roughness > 0.90:
                errors.append(f"Material '{mat.name}' roughnessFactor={roughness:.2f} out of textile range [0.30, 0.90].")
            if tex_idx is None:
                errors.append(f"Material '{mat.name}' has no baseColorTexture assigned.")
            mats_summary.append({
                "name": mat.name,
                "metallicFactor": metallic,
                "roughnessFactor": roughness,
                "doubleSided": bool(mat.doubleSided),
                "hasBaseColorTexture": tex_idx is not None,
            })

        img_summary = []
        blob = gltf.binary_blob()
        if not gltf.images:
            errors.append("No embedded texture images present in GLB.")
        for img in gltf.images or []:
            if img.bufferView is not None and blob:
                bv = gltf.bufferViews[img.bufferView]
                off = bv.byteOffset or 0
                raw = blob[off : off + bv.byteLength]
                pil_img = Image.open(io.BytesIO(raw))
                w, h = pil_img.size
                if w < 1024 or h < 1024:
                    errors.append(f"Embedded texture image resolution {w}x{h} is below 1024x1024 minimum.")
                img_summary.append({"size": [w, h], "mode": pil_img.mode, "byteLength": bv.byteLength})

        scene = trimesh.load(glb_path, force="scene", process=False)
        uv_checked = 0
        for gname, mesh in scene.geometry.items():
            uv = getattr(mesh.visual, "uv", None)
            if uv is None or len(uv) != len(mesh.vertices):
                errors.append(f"Component '{gname}' missing or mismatched UV coordinates.")
            elif not ((uv >= -1e-5).all() and (uv <= 1.0 + 1e-5).all()):
                errors.append(f"Component '{gname}' has UV coordinates outside [0, 1].")
            else:
                uv_checked += 1

        return {
            "passed": len(errors) == 0,
            "materials": mats_summary,
            "embedded_images": img_summary,
            "uv_valid_components": uv_checked,
            "errors": errors,
        }

    @classmethod
    def _inspect_mesh_measurements(
        cls,
        glb_path: str,
        geom_check: Dict[str, Any],
        spec: Dict[str, Any],
        size_label: str,
    ) -> Dict[str, Any]:
        if not geom_check.get("passed"):
            return {"passed": False, "errors": ["Geometry check failed; dimensional audit skipped"]}

        scene = trimesh.load(glb_path, force="scene", process=False)
        geoms = dict(scene.geometry)
        errors: List[str] = []
        tol_3d = DIMENSIONAL_TOLERANCE_CONTRACT["3d_assembled_cm"]

        t_half_chest = float(spec.get("half_chest_width_cm", 54.0))
        t_back_len = float(spec.get("back_length_cm", 67.0))
        t_shoulder = float(spec.get("shoulder_breadth_cm", 50.0))
        t_sleeve_len = float(spec.get("sleeve_length_cm", 17.0))
        t_sleeve_open = float(spec.get("sleeve_opening_cm", 20.5))
        t_collar_circ = float(spec.get("collar_circumference_cm", 44.0))
        t_hem_width = float(spec.get("hem_width_cm", 53.0))

        front = geoms.get("PANEL-FRONT-TORSO")
        back = geoms.get("PANEL-BACK-TORSO")
        collar = geoms.get("PANEL-COLLAR-RIB")
        hem = geoms.get("PANEL-HEM-BAND")
        slv_l = geoms.get("PANEL-SLEEVE-L")
        if not (front and back and collar and hem and slv_l):
            return {"passed": False, "errors": ["Missing required pattern components for dimensional measurement."]}

        torso = trimesh.Trimesh(
            vertices=np.vstack([front.vertices, back.vertices]),
            faces=np.vstack([front.faces, back.faces + len(front.vertices)]),
            process=True,
        )

        # 1. Torso Chest Circumference (below armhole, excluding sleeves)
        slv_inner_x_min = float(slv_l.vertices[:, 0].min())
        underarm_y = float(slv_l.vertices[slv_l.vertices[:, 0] <= slv_inner_x_min + 0.012, 1].min())
        chest_loops = _slice_closed_loops_at_y(torso, underarm_y - 0.015)
        chest_circ_3d_cm = chest_loops[0]["perimeter_cm"] if chest_loops else 0.0
        chest_x_span_3d_cm = chest_loops[0]["x_span_cm"] if chest_loops else 0.0
        chest_z_span_3d_cm = chest_loops[0]["z_span_cm"] if chest_loops else 0.0
        target_3d_chest_circ = 2.0 * t_half_chest
        chest_err = round(abs(chest_circ_3d_cm - target_3d_chest_circ), 2)
        chest_tol = tol_3d["torso_chest_circumference_cm"]["tolerance_cm"]
        chest_ok = chest_err <= chest_tol
        if not chest_ok:
            errors.append(f"3D torso_chest_circumference_cm={chest_circ_3d_cm} vs {target_3d_chest_circ} (err {chest_err} > {chest_tol})")

        # 2. Back Length (HPS to Hem bottom)
        back_len_3d_cm = round((float(back.vertices[:, 1].max()) - float(hem.vertices[:, 1].min())) * 100.0, 2)
        len_err = round(abs(back_len_3d_cm - t_back_len), 2)
        len_tol = tol_3d["back_length_hps_to_hem_cm"]["tolerance_cm"]
        len_ok = len_err <= len_tol
        if not len_ok:
            errors.append(f"3D back_length_hps_to_hem_cm={back_len_3d_cm} vs {t_back_len} (err {len_err} > {len_tol})")

        # 3. Shoulder Breadth (seam-to-seam across back)
        shoulder_3d_cm = round(float(back.bounds[1][0] - back.bounds[0][0]) * 100.0, 2)
        sh_err = round(abs(shoulder_3d_cm - t_shoulder), 2)
        sh_tol = tol_3d["shoulder_breadth_seam_to_seam_cm"]["tolerance_cm"]
        sh_ok = sh_err <= sh_tol
        if not sh_ok:
            errors.append(f"3D shoulder_breadth_seam_to_seam_cm={shoulder_3d_cm} vs {t_shoulder} (err {sh_err} > {sh_tol})")

        # 4. Sleeve Centerline Length (actual armhole cap midpoint -> cuff opening centroid)
        loops = geom_check.get("boundary_loops", [])
        cuff_l_loop = next((lp for lp in loops if lp["classified_role"] == "Left Sleeve Cuff Opening"), None)
        # Armhole cap midpoint computed directly from sleeve vertices matching front/back armhole boundary
        armhole_tree = cKDTree(np.vstack([front.vertices, back.vertices]))
        d_arm, _ = armhole_tree.query(slv_l.vertices)
        cap_pts = slv_l.vertices[d_arm < 0.001]
        armhole_mid_l = 0.5 * (cap_pts[np.argmax(cap_pts[:, 1])] + cap_pts[np.argmin(cap_pts[:, 1])]) if len(cap_pts) > 0 else slv_l.vertices.mean(axis=0)
        cuff_l_cen = np.array(cuff_l_loop["centroid_m"]) if cuff_l_loop else slv_l.vertices.mean(axis=0)
        sleeve_len_3d_cm = round(float(np.linalg.norm(cuff_l_cen - armhole_mid_l)) * 100.0, 2)
        slv_err = round(abs(sleeve_len_3d_cm - t_sleeve_len), 2)
        slv_tol = tol_3d["sleeve_centerline_length_cm"]["tolerance_cm"]
        slv_ok = slv_err <= slv_tol
        if not slv_ok:
            errors.append(f"3D sleeve_centerline_length_cm={sleeve_len_3d_cm} vs {t_sleeve_len} (err {slv_err} > {slv_tol})")

        # 5. Collar Opening Circumference (top finished edge)
        neck_loop = next((lp for lp in loops if lp["classified_role"] == "Neckline Opening"), None)
        collar_open_3d_cm = neck_loop["perimeter_cm"] if neck_loop else 0.0
        col_err = round(abs(collar_open_3d_cm - t_collar_circ), 2)
        col_tol = tol_3d["collar_opening_circumference_cm"]["tolerance_cm"]
        col_ok = col_err <= col_tol
        if not col_ok:
            errors.append(f"3D collar_opening_circumference_cm={collar_open_3d_cm} vs {t_collar_circ} (err {col_err} > {col_tol})")

        # 6. Bottom Hem Perimeter
        hem_loop = next((lp for lp in loops if lp["classified_role"] == "Bottom Hem Opening"), None)
        hem_perim_3d_cm = hem_loop["perimeter_cm"] if hem_loop else 0.0
        target_3d_hem_perim = 2.0 * t_hem_width
        hem_err = round(abs(hem_perim_3d_cm - target_3d_hem_perim), 2)
        hem_tol = tol_3d["bottom_hem_perimeter_cm"]["tolerance_cm"]
        hem_ok = hem_err <= hem_tol
        if not hem_ok:
            errors.append(f"3D bottom_hem_perimeter_cm={hem_perim_3d_cm} vs {target_3d_hem_perim} (err {hem_err} > {hem_tol})")

        # 7. Sleeve Cuff Circumference
        cuff_perim_3d_cm = cuff_l_loop["perimeter_cm"] if cuff_l_loop else 0.0
        target_3d_cuff_perim = 2.0 * t_sleeve_open
        cuff_err = round(abs(cuff_perim_3d_cm - target_3d_cuff_perim), 2)
        cuff_tol = tol_3d["sleeve_cuff_circumference_cm"]["tolerance_cm"]
        cuff_ok = cuff_err <= cuff_tol
        if not cuff_ok:
            errors.append(f"3D sleeve_cuff_circumference_cm={cuff_perim_3d_cm} vs {target_3d_cuff_perim} (err {cuff_err} > {cuff_tol})")

        return {
            "passed": len(errors) == 0,
            "errors": errors,
            "dimensions_3d_assembled_cm": {
                "torso_chest_circumference_cm": {"actual": chest_circ_3d_cm, "target": target_3d_chest_circ, "abs_error_cm": chest_err, "tolerance_cm": chest_tol, "passed": chest_ok, "torso_x_span_cm": chest_x_span_3d_cm, "torso_z_span_cm": chest_z_span_3d_cm},
                "back_length_hps_to_hem_cm": {"actual": back_len_3d_cm, "target": t_back_len, "abs_error_cm": len_err, "tolerance_cm": len_tol, "passed": len_ok},
                "shoulder_breadth_seam_to_seam_cm": {"actual": shoulder_3d_cm, "target": t_shoulder, "abs_error_cm": sh_err, "tolerance_cm": sh_tol, "passed": sh_ok},
                "sleeve_centerline_length_cm": {"actual": sleeve_len_3d_cm, "target": t_sleeve_len, "abs_error_cm": slv_err, "tolerance_cm": slv_tol, "passed": slv_ok},
                "collar_opening_circumference_cm": {"actual": collar_open_3d_cm, "target": t_collar_circ, "abs_error_cm": col_err, "tolerance_cm": col_tol, "passed": col_ok},
                "bottom_hem_perimeter_cm": {"actual": hem_perim_3d_cm, "target": target_3d_hem_perim, "abs_error_cm": hem_err, "tolerance_cm": hem_tol, "passed": hem_ok},
                "sleeve_cuff_circumference_cm": {"actual": cuff_perim_3d_cm, "target": target_3d_cuff_perim, "abs_error_cm": cuff_err, "tolerance_cm": cuff_tol, "passed": cuff_ok},
            },
        }

    @staticmethod
    def _eval_panel_z_at_xy(panel_mesh: trimesh.Trimesh, pts_xyz: np.ndarray) -> np.ndarray:
        """
        Evaluate exact panel Z at query (x, y) points using actual mesh triangles (not convex-hull interpolation
        so neck openings and armhole cutouts are never bridged across). Returns NaN where no triangle covers (x, y).
        """
        tris = panel_mesh.triangles  # (T, 3, 3)
        a = tris[:, 0, :]
        b = tris[:, 1, :]
        c = tris[:, 2, :]
        v0x = c[:, 0] - a[:, 0]
        v0y = c[:, 1] - a[:, 1]
        v1x = b[:, 0] - a[:, 0]
        v1y = b[:, 1] - a[:, 1]
        dot00 = v0x * v0x + v0y * v0y
        dot01 = v0x * v1x + v0y * v1y
        dot11 = v1x * v1x + v1y * v1y
        denom = dot00 * dot11 - dot01 * dot01
        valid_tri = np.abs(denom) > 1e-12

        out_z = np.full(len(pts_xyz), np.nan, dtype=np.float64)
        px = pts_xyz[:, 0:1]
        py = pts_xyz[:, 1:2]
        v2x = px - a[:, 0][None, :]
        v2y = py - a[:, 1][None, :]
        dot02 = v0x[None, :] * v2x + v0y[None, :] * v2y
        dot12 = v1x[None, :] * v2x + v1y[None, :] * v2y

        inv_denom = np.zeros_like(denom)
        inv_denom[valid_tri] = 1.0 / denom[valid_tri]
        u = (dot11[None, :] * dot02 - dot01[None, :] * dot12) * inv_denom[None, :]
        v = (dot00[None, :] * dot12 - dot01[None, :] * dot02) * inv_denom[None, :]
        inside = valid_tri[None, :] & (u >= -1e-5) & (v >= -1e-5) & ((u + v) <= 1.0 + 1e-5)

        z_tri = a[:, 2][None, :] + u * (c[:, 2] - a[:, 2])[None, :] + v * (b[:, 2] - a[:, 2])[None, :]
        for idx in range(len(pts_xyz)):
            hits = np.where(inside[idx])[0]
            if len(hits) > 0:
                out_z[idx] = float(np.mean(z_tri[idx, hits]))
        return out_z

    @staticmethod
    def _closest_points_on_triangles(avatar_mesh: trimesh.Trimesh, query_pts: np.ndarray, k_verts: int = 10) -> np.ndarray:
        """Exact closest-triangle signed distance (cm) without rtree, using vertex cKDTree + incident triangles."""
        v = np.asarray(avatar_mesh.vertices, dtype=np.float64)
        f = np.asarray(avatar_mesh.faces, dtype=np.int32)
        tris_all = v[f]
        fnorms = np.asarray(avatar_mesh.face_normals, dtype=np.float64)

        v_to_f = defaultdict(list)
        for fi, (a_i, b_i, c_i) in enumerate(f):
            v_to_f[int(a_i)].append(fi)
            v_to_f[int(b_i)].append(fi)
            v_to_f[int(c_i)].append(fi)

        tree = cKDTree(v)
        _, nn_idx = tree.query(query_pts, k=k_verts)
        signed_cm = np.zeros(len(query_pts), dtype=np.float64)

        for qi in range(len(query_pts)):
            cand = set()
            for vi in nn_idx[qi]:
                cand.update(v_to_f[int(vi)])
            fids = np.array(sorted(cand), dtype=np.int32)
            tris = tris_all[fids]
            p = query_pts[qi]
            a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
            ab, ac, ap = b - a, c - a, p - a
            d1 = np.einsum("ij,ij->i", ab, ap)
            d2 = np.einsum("ij,ij->i", ac, ap)
            d3 = np.einsum("ij,ij->i", ab, p - b)
            d4 = np.einsum("ij,ij->i", ac, p - b)
            d5 = np.einsum("ij,ij->i", ab, p - c)
            d6 = np.einsum("ij,ij->i", ac, p - c)
            vc, vb, va = d1 * d4 - d3 * d2, d5 * d2 - d1 * d6, d3 * d6 - d5 * d4
            c_pts = np.zeros_like(a)
            for mi in range(len(fids)):
                if d1[mi] <= 0.0 and d2[mi] <= 0.0:
                    c_pts[mi] = a[mi]
                elif d3[mi] >= 0.0 and d4[mi] <= d3[mi]:
                    c_pts[mi] = b[mi]
                elif vc[mi] <= 0.0 and d1[mi] >= 0.0 and d3[mi] <= 0.0:
                    c_pts[mi] = a[mi] + (d1[mi] / (d1[mi] - d3[mi] + 1e-18)) * ab[mi]
                elif d6[mi] >= 0.0 and d5[mi] <= d6[mi]:
                    c_pts[mi] = c[mi]
                elif vb[mi] <= 0.0 and d2[mi] >= 0.0 and d6[mi] <= 0.0:
                    c_pts[mi] = a[mi] + (d2[mi] / (d2[mi] - d6[mi] + 1e-18)) * ac[mi]
                elif va[mi] <= 0.0 and (d4[mi] - d3[mi]) >= 0.0 and (d5[mi] - d6[mi]) >= 0.0:
                    w = (d4[mi] - d3[mi]) / ((d4[mi] - d3[mi]) + (d5[mi] - d6[mi]) + 1e-18)
                    c_pts[mi] = b[mi] + w * (c[mi] - b[mi])
                else:
                    denom = 1.0 / (va[mi] + vb[mi] + vc[mi] + 1e-18)
                    c_pts[mi] = a[mi] + ab[mi] * (vb[mi] * denom) + ac[mi] * (vc[mi] * denom)
            dists = np.linalg.norm(c_pts - p, axis=1)
            bi = int(np.argmin(dists))
            sign = 1.0 if np.dot(p - c_pts[bi], fnorms[fids[bi]]) >= 0.0 else -1.0
            signed_cm[qi] = dists[bi] * sign * 100.0
        return signed_cm

    @staticmethod
    def _ray_contains_plus_z(avatar_mesh: trimesh.Trimesh, pts: np.ndarray) -> np.ndarray:
        """Exact +Z ray-parity inside-volume containment test for watertight baseline avatar mesh."""
        tris = np.asarray(avatar_mesh.triangles, dtype=np.float64)
        v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
        tmin_xy = tris[:, :, :2].min(axis=1) - 1e-9
        tmax_xy = tris[:, :, :2].max(axis=1) + 1e-9
        tmax_z = tris[:, :, 2].max(axis=1) + 1e-9
        e1, e2 = v1 - v0, v2 - v0
        det = e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]
        valid_det = np.abs(det) > 1e-12
        inside = np.zeros(len(pts), dtype=bool)
        for i, p in enumerate(pts):
            cand = (
                valid_det
                & (tmax_z >= p[2])
                & (tmin_xy[:, 0] <= p[0]) & (tmax_xy[:, 0] >= p[0])
                & (tmin_xy[:, 1] <= p[1]) & (tmax_xy[:, 1] >= p[1])
            )
            idx = np.where(cand)[0]
            if len(idx) == 0:
                continue
            dx, dy = p[0] - v0[idx, 0], p[1] - v0[idx, 1]
            inv_d = 1.0 / det[idx]
            u = (dx * e2[idx, 1] - dy * e2[idx, 0]) * inv_d
            v = (e1[idx, 0] * dy - e1[idx, 1] * dx) * inv_d
            hit = (u >= -1e-7) & (v >= -1e-7) & ((u + v) <= 1.0 + 1e-7)
            if not np.any(hit):
                continue
            z_hit = v0[idx[hit], 2] + u[hit] * e1[idx[hit], 2] + v[hit] * e2[idx[hit], 2]
            inside[i] = (int(np.sum(z_hit > p[2] + 1e-7)) % 2) == 1
        return inside

    @classmethod
    def _inspect_avatar_fit_clearance(cls, glb_path: str, avatar_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Inspects avatar fit & clearance on static A-pose baseline mannequin using BOTH:
        1) Full-3D closest-surface signed distance + watertight inside-volume containment across ALL 7 components
        2) Legacy 6 axial/alignment zones (front_torso, rear_scapula, shoulder/armhole, underarm, sleeve-to-arm, hem).
        """
        if not avatar_path:
            avatar_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "..", "frontend", "public", "avatars", "anny_baseline_male.glb"
            )
        anny = list(trimesh.load(avatar_path, force="scene").geometry.values())[0]
        sc = trimesh.load(glb_path, force="scene", process=False)
        back = sc.geometry.get("PANEL-BACK-TORSO")
        front = sc.geometry.get("PANEL-FRONT-TORSO")
        slv_l = sc.geometry.get("PANEL-SLEEVE-L")
        slv_r = sc.geometry.get("PANEL-SLEEVE-R")
        hem = sc.geometry.get("PANEL-HEM-BAND")

        # Full-3D closest-surface signed distance & containment across every component
        region_thresholds = {
            "PANEL-FRONT-TORSO": {"min_cm": 0.25, "strict": False, "excessive_cm": 12.0},
            "PANEL-BACK-TORSO": {"min_cm": 0.25, "strict": False, "excessive_cm": 12.0},
            "PANEL-COLLAR-RIB": {"min_cm": 0.25, "strict": False, "excessive_cm": 8.0},
            "PANEL-HEM-BAND": {"min_cm": 0.25, "strict": False, "excessive_cm": 14.0},
            "PANEL-SLEEVE-L": {"min_cm": 0.0, "strict": True, "excessive_cm": 10.0},
            "PANEL-SLEEVE-R": {"min_cm": 0.0, "strict": True, "excessive_cm": 10.0},
            "PANEL-POCKET-CHEST": {"min_cm": 0.25, "strict": False, "excessive_cm": 12.0},
        }
        full_3d_regions: Dict[str, Any] = {}
        fit_errors: List[str] = []
        total_inside_verts = 0
        total_penetrating_verts = 0
        excessive_clearance_zones: Dict[str, Any] = {}

        for pname, gmesh in sc.geometry.items():
            pts = np.asarray(gmesh.vertices, dtype=np.float64)
            signed_cm = cls._closest_points_on_triangles(anny, pts)
            inside_mask = cls._ray_contains_plus_z(anny, pts) if anny.is_watertight else (signed_cm < 0.0)

            cfg = region_thresholds.get(pname, {"min_cm": 0.25, "strict": False, "excessive_cm": 12.0})
            min_req = cfg["min_cm"]
            exc_thr = cfg["excessive_cm"]
            below_mask = (signed_cm <= min_req) if cfg["strict"] else (signed_cm < min_req)
            pen_mask = (signed_cm < 0.0) | inside_mask
            exc_mask = signed_cm > exc_thr

            pen_cnt = int(np.sum(pen_mask))
            in_cnt = int(np.sum(inside_mask))
            below_cnt = int(np.sum(below_mask))
            exc_cnt = int(np.sum(exc_mask))
            total_inside_verts += in_cnt
            total_penetrating_verts += pen_cnt

            min_val = round(float(signed_cm.min()), 3)
            mean_val = round(float(signed_cm.mean()), 3)
            p95_val = round(float(np.percentile(signed_cm, 95)), 3)
            max_val = round(float(signed_cm.max()), 3)

            if pen_cnt > 0 or in_cnt > 0:
                fit_errors.append(
                    f"{pname}: {pen_cnt} penetrating vertices ({in_cnt} strictly inside avatar volume), min_clearance={min_val:.3f} cm."
                )
            elif below_cnt > 0:
                op = ">" if cfg["strict"] else ">="
                fit_errors.append(
                    f"{pname}: {below_cnt} vertices below minimum clearance {op} {min_req:.2f} cm (min={min_val:.3f} cm)."
                )

            if exc_cnt > 0:
                excessive_clearance_zones[pname] = {
                    "count": exc_cnt,
                    "threshold_cm": exc_thr,
                    "max_cm": max_val,
                }

            full_3d_regions[pname] = {
                "vertex_count": int(len(pts)),
                "min_cm": min_val,
                "mean_cm": mean_val,
                "p95_cm": p95_val,
                "max_cm": max_val,
                "penetrating_vertices": pen_cnt,
                "inside_volume_vertices": in_cnt,
                "below_min_clearance_vertices": below_cnt,
                "required_min_clearance_cm": min_req,
                "strict_greater": bool(cfg["strict"]),
                "excessive_clearance_vertices": exc_cnt,
                "excessive_threshold_cm": exc_thr,
            }

        # 1 & 2. Front torso & rear scapula clearance (exact triangle projection, |x| <= 0.215m)
        rear_protruding = 0
        max_rear_prot_cm = 0.0
        rear_min_clearance_cm = None
        if back is not None:
            sub = anny.vertices[
                (anny.vertices[:, 1] >= 1.08)
                & (anny.vertices[:, 1] <= 1.35)
                & (anny.vertices[:, 2] < -0.08)
                & (np.abs(anny.vertices[:, 0]) <= 0.215)
            ]
            gz = cls._eval_panel_z_at_xy(back, sub)
            valid = ~np.isnan(gz)
            if np.any(valid):
                clearances = (sub[valid, 2] - gz[valid]) * 100.0
                rear_min_clearance_cm = round(float(clearances.min()), 2)
                mask = sub[valid, 2] < gz[valid]
                rear_protruding = int(np.sum(mask))
                if rear_protruding > 0:
                    max_rear_prot_cm = round(float((-clearances[mask]).max()), 2)

        front_protruding = 0
        max_front_prot_cm = 0.0
        front_min_clearance_cm = None
        if front is not None:
            sub_f = anny.vertices[
                (anny.vertices[:, 1] >= 1.08)
                & (anny.vertices[:, 1] <= 1.35)
                & (anny.vertices[:, 2] > -0.08)
                & (np.abs(anny.vertices[:, 0]) <= 0.215)
            ]
            gz_f = cls._eval_panel_z_at_xy(front, sub_f)
            valid_f = ~np.isnan(gz_f)
            if np.any(valid_f):
                clearances_f = (gz_f[valid_f] - sub_f[valid_f, 2]) * 100.0
                front_min_clearance_cm = round(float(clearances_f.min()), 2)
                mask_f = sub_f[valid_f, 2] > gz_f[valid_f]
                front_protruding = int(np.sum(mask_f))
                if front_protruding > 0:
                    max_front_prot_cm = round(float((-clearances_f[mask_f]).max()), 2)

        # 3. Shoulder & armhole clearance (top shoulder seam above Anny deltoid/trapezius crest)
        shoulder_clearance_cm = None
        armhole_z_span_cm = None
        if back is not None and front is not None:
            sh_garment_min_y = float(back.vertices[np.abs(back.vertices[:, 0]) >= 0.08, 1].max())
            # Anny upper shoulder crest in [0.09, 0.21] |x|, y in [1.18, 1.33]
            sh_anny = anny.vertices[(np.abs(anny.vertices[:, 0]) >= 0.09) & (np.abs(anny.vertices[:, 0]) <= 0.21) & (anny.vertices[:, 1] >= 1.18) & (anny.vertices[:, 1] <= 1.33)]
            anny_shoulder_crest_y = float(sh_anny[:, 1].max()) if len(sh_anny) else 1.27
            shoulder_clearance_cm = round((sh_garment_min_y - anny_shoulder_crest_y) * 100.0, 2)
            x_edge = float(front.vertices[:, 0].max())
            arm_f_z = float(front.vertices[front.vertices[:, 0] >= x_edge - 0.015, 2].max())
            arm_b_z = float(back.vertices[back.vertices[:, 0] >= x_edge - 0.015, 2].min())
            armhole_z_span_cm = round((arm_f_z - arm_b_z) * 100.0, 2)

        # 4. Underarm clearance (garment underarm seam level relative to Anny axilla y~1.16)
        underarm_clearance_cm = None
        if slv_l is not None:
            slv_inner_x = float(slv_l.vertices[:, 0].min())
            garment_underarm_y = float(slv_l.vertices[slv_l.vertices[:, 0] <= slv_inner_x + 0.012, 1].min())
            axilla = anny.vertices[(anny.vertices[:, 0] >= 0.17) & (anny.vertices[:, 0] <= 0.24) & (anny.vertices[:, 1] >= 1.12) & (anny.vertices[:, 1] <= 1.21)]
            anny_axilla_y = float(axilla[:, 1].min()) if len(axilla) else 1.16
            underarm_clearance_cm = round((anny_axilla_y - garment_underarm_y) * 100.0, 2)

        # 5. Sleeve-to-arm alignment (deviation between sleeve centerline and Anny arm centroid axis)
        sleeve_arm_offset_cm = {}
        for side_lbl, slv_mesh, sign_x in [("left", slv_l, 1.0), ("right", slv_r, -1.0)]:
            if slv_mesh is not None:
                c_g = slv_mesh.vertices.mean(axis=0)
                arm_pts = anny.vertices[
                    (sign_x * anny.vertices[:, 0] >= 0.22)
                    & (sign_x * anny.vertices[:, 0] <= 0.36)
                    & (anny.vertices[:, 1] >= 0.96)
                    & (anny.vertices[:, 1] <= 1.22)
                ]
                if len(arm_pts) > 0:
                    c_a = arm_pts.mean(axis=0)
                    sleeve_arm_offset_cm[side_lbl] = round(float(np.linalg.norm(c_g[[1, 2]] - c_a[[1, 2]])) * 100.0, 2)

        # 6. Hem and body clearance (garment bottom hem x-ease + lower-torso/hem front & rear Z clearance)
        hem_clearance_cm = None
        lower_front_prot = 0
        lower_rear_prot = 0
        if hem is not None and front is not None and back is not None:
            hem_y = float(hem.vertices[:, 1].mean())
            hem_x_span = float(hem.vertices[:, 0].max() - hem.vertices[:, 0].min())
            anny_hip = anny.vertices[np.abs(anny.vertices[:, 1] - hem_y) <= 0.03]
            if len(anny_hip) > 0:
                anny_hip_x_span = float(anny_hip[:, 0].max() - anny_hip[:, 0].min())
                hem_clearance_cm = round(((hem_x_span - anny_hip_x_span) * 0.5) * 100.0, 2)
            hem_z_mid = float(hem.vertices[:, 2].mean())
            f_hem_idx = np.where(hem.triangles[:, :, 2].mean(axis=1) >= hem_z_mid)[0]
            b_hem_idx = np.where(hem.triangles[:, :, 2].mean(axis=1) < hem_z_mid)[0]
            f_hem = trimesh.Trimesh(vertices=hem.vertices, faces=hem.faces[f_hem_idx], process=False)
            b_hem = trimesh.Trimesh(vertices=hem.vertices, faces=hem.faces[b_hem_idx], process=False)
            lower_front_mesh = trimesh.util.concatenate([front, f_hem])
            lower_back_mesh = trimesh.util.concatenate([back, b_hem])
            sub_lf = anny.vertices[(anny.vertices[:, 1] >= hem.vertices[:, 1].min()) & (anny.vertices[:, 1] < 1.08) & (anny.vertices[:, 2] > -0.09) & (np.abs(anny.vertices[:, 0]) <= 0.215)]
            sub_lr = anny.vertices[(anny.vertices[:, 1] >= hem.vertices[:, 1].min()) & (anny.vertices[:, 1] < 1.08) & (anny.vertices[:, 2] < -0.10) & (np.abs(anny.vertices[:, 0]) <= 0.215)]
            gz_lf = cls._eval_panel_z_at_xy(lower_front_mesh, sub_lf)
            gz_lr = cls._eval_panel_z_at_xy(lower_back_mesh, sub_lr)
            lower_front_prot = int(np.sum((~np.isnan(gz_lf)) & (sub_lf[:, 2] > gz_lf)))
            lower_rear_prot = int(np.sum((~np.isnan(gz_lr)) & (sub_lr[:, 2] < gz_lr)))

        return {
            "avatar_file": os.path.basename(avatar_path),
            "avatar_is_watertight": bool(anny.is_watertight),
            "avatar_vertex_count": int(len(anny.vertices)),
            "avatar_face_count": int(len(anny.faces)),
            "avatar_bounds_cm": [round(float(x) * 100.0, 2) for x in (anny.bounds[1] - anny.bounds[0])],
            "fit_clearance_passed": len(fit_errors) == 0,
            "fit_clearance_errors": fit_errors,
            "fit_clearance_contract": {
                "scope": "static_a_pose_baseline_mannequin_only",
                "torso_collar_hem_min_clearance_cm": 0.25,
                "sleeve_min_clearance_cm": "> 0.00",
                "inside_avatar_volume_allowed": 0,
                "disclaimer": "Static A-pose clearance applies strictly to baseline mannequin anny_baseline_male.glb and does not claim universal shopper fit.",
            },
            "total_penetrating_vertices_3d": total_penetrating_verts,
            "total_inside_avatar_vertices": total_inside_verts,
            "full_3d_clearance_by_region": full_3d_regions,
            "excessive_clearance_summary": excessive_clearance_zones,
            "front_torso_clearance": {"protruding_vertices": front_protruding, "max_protrusion_cm": max_front_prot_cm, "min_clearance_cm": front_min_clearance_cm},
            "rear_scapula_clearance": {"protruding_vertices": rear_protruding, "max_protrusion_cm": max_rear_prot_cm, "min_clearance_cm": rear_min_clearance_cm},
            "shoulder_and_armhole_clearance": {"shoulder_crest_clearance_cm": shoulder_clearance_cm, "armhole_z_span_cm": armhole_z_span_cm},
            "underarm_clearance": {"axilla_drop_clearance_cm": underarm_clearance_cm},
            "sleeve_to_arm_alignment": {"yz_centroid_offset_cm": sleeve_arm_offset_cm},
            "hem_and_body_clearance": {"lateral_ease_per_side_cm": hem_clearance_cm, "lower_front_protruding_vertices": lower_front_prot, "lower_rear_protruding_vertices": lower_rear_prot},
            "rear_scapula_protruding_vertices": rear_protruding,
            "max_rear_protrusion_cm": max_rear_prot_cm,
            "front_chest_protruding_vertices": front_protruding,
            "max_front_protrusion_cm": max_front_prot_cm,
            "note": "Avatar fit metrics are isolated from garment geometry QA and apply strictly to baseline A-pose mannequin.",
        }

    @classmethod
    def _inspect_texture_atlas(cls, atlas_path: str) -> Dict[str, Any]:
        if not os.path.exists(atlas_path):
            return {"passed": False, "error": f"Texture atlas missing: {atlas_path}"}
        try:
            im = Image.open(atlas_path)
            w, h = im.size
            is_valid_res = w >= 1024 and h >= 1024
            file_size_kb = os.path.getsize(atlas_path) / 1024.0
            return {
                "passed": is_valid_res,
                "resolution": f"{w}x{h}",
                "channels": im.mode,
                "file_size_kb": round(file_size_kb, 1),
                "is_pbr_ready": is_valid_res and im.mode in ["RGB", "RGBA"],
            }
        except Exception as err:
            return {"passed": False, "error": str(err)}
