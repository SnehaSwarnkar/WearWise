"""
WearWise Pattern-First Digital Garment Builder
==============================================
Constructs genuine 2D pattern components (ordered 2D outlines, edge IDs, notches,
seam allowances, grainlines, and SVG exports), validates explicit 1-to-1 seam-edge
relationships and surface attachment paths, and assembles static 3D garment meshes
with PBR texture mapping completely independent of avatar skin cropping.
"""

from __future__ import annotations

import os
import math
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from PIL import Image
import trimesh
from trimesh.visual import TextureVisuals
from trimesh.visual.material import PBRMaterial
from scipy.interpolate import LinearNDInterpolator
from shapely.geometry import Polygon as ShapelyPolygon


# Reference upright Anny anthropometric landmarks (meters, Y-up, +Z forward)
# Used ONLY as an external fitting/clearance reference, never as a mesh source.
ANNY_UPRIGHT_FIT_FRAME = {
    "y_hps": 1.355,           # Clear above Anny neck/trapezius ridge (y=1.319 at x=0.08)
    "y_underarm": 1.085,      # Size M canonical armpit separation level
    "y_drop_sh": 1.275,       # Size M canonical dropped shoulder seam tip
    "z_center": -0.084,       # Torso centerline Z
    "arm_axis_origin_l": np.array([0.215, 1.185, -0.084]),
    "arm_axis_dir_l": np.array([0.5145, -0.8548, 0.0641]),
}

# Authoritative M-canonical Pattern Grading Specification (ISO 8559-2 / BS 4952 aligned)
PATTERN_GRADING_SPEC = {
    "canonical_base_size": "M",
    "canonical_base_asset": "TSH-WW-CREW-001_M_prototype_rev2.glb",
    "grading_method": "2d_component_pattern_grading_then_3d_assembly",
    "arbitrary_uniform_glb_scaling_prohibited": True,
    "rules_relative_to_M": {
        "half_chest_width_cm": {"S": -4.0, "M": 0.0, "L": 4.0, "rule": "Distribute symmetrically across front/back superellipse torso panels (3D chest circ +/-8.0 cm)."},
        "back_length_cm": {"S": -3.0, "M": 0.0, "L": 3.0, "rule": "Anchor HPS at y=1.355 m and grade lower torso hem downward (hem band height fixed at 2.80 cm)."},
        "shoulder_breadth_cm": {"S": -3.0, "M": 0.0, "L": 3.0, "rule": "Grade dropped-shoulder tip +/-1.5 cm per side following shoulder slope dy/dx=0.45."},
        "armhole_depth_cm": {"S": -1.5, "M": 0.0, "L": 1.5, "rule": "Shift underarm seam level y_underarm +1.5 cm (S) / -1.5 cm (L) relative to M=1.085 m."},
        "sleeve_length_cm": {"S": -2.0, "M": 0.0, "L": 2.0, "rule": "Grade sleeve centerline length along A-pose arm axis from armhole cap midpoint to cuff opening centroid."},
        "sleeve_opening_cm": {"S": -1.0, "M": 0.0, "L": 1.0, "rule": "Grade cuff flat half-width +/-1.0 cm (+/-2.0 cm cuff circumference)."},
        "collar_circumference_cm": {"S": -2.0, "M": 0.0, "L": 2.0, "rule": "Grade finished collar top opening circumference +/-2.0 cm and scale neckline aperture x_neck, dips proportionally (C_open / 44.0)."},
        "hem_width_cm": {"S": -4.0, "M": 0.0, "L": 4.0, "rule": "Grade hem flat half-width +/-4.0 cm (hem perimeter +/-8.0 cm)."},
        "chest_pocket_cm": {"S": {"width": 11.0, "height": 13.0}, "M": {"width": 11.5, "height": 13.5}, "L": {"width": 12.0, "height": 14.0}, "rule": "Grade pocket width +/-0.5 cm, height +/-0.5 cm, and placement proportional to chest half-width and back length while maintaining 3.5 mm normal relief."},
    },
    "seam_allowances_cm": {
        "torso_and_sleeves": 1.0,
        "collar_and_hem_bands": 0.7,
        "pocket_patch": 1.0,
    },
    "collar_closure_convention": {
        "cause": "conical_ring_curvature_development",
        "explanation": "2D pattern unrolls the tapered neckband onto a straight strip (end slant = sqrt(((C_seam - C_open)/2)^2 + h^2), e.g., 4.54 cm on M), whereas closing the ring in 3D distributes radial taper uniformly around the oval aperture (3D join meridian = sqrt(h^2 + delta_r_join^2), e.g., 3.10 cm on M). Cutting edge adds 0.70 cm SA at top and bottom.",
    },
    "pocket_attachment_convention": {
        "mapping": "planar_chest_box_to_curved_3d_torso_surface_with_normal_relief",
        "explanation": "Planar 2D U-stitch path (e.g., 37.33 cm on M) projects onto the curved convex front torso superellipse + right shoulder slope, adding surface Z-curvature arc length (~+2.66 cm on M -> 39.99 cm 3D) plus 3.5 mm normal applique relief.",
    },
}


def _solve_superellipse_axes(
    target_half_perim_cm: float,
    aspect_b_over_a: float = 0.68,
    exponent_p: float = 2.6,
) -> Tuple[float, float]:
    """Solves superellipse semi-axes (a, b) in meters for an exact 2D arc half-perimeter."""
    t = np.linspace(0.0, np.pi, 1200)
    ux = np.sign(np.cos(t)) * (np.abs(np.cos(t)) ** (2.0 / exponent_p))
    uz = aspect_b_over_a * np.sign(np.sin(t)) * (np.abs(np.sin(t)) ** (2.0 / exponent_p))
    unit_hp = float(np.linalg.norm(np.diff(np.column_stack([ux, uz]), axis=0), axis=1).sum())
    a_m = (target_half_perim_cm / unit_hp) / 100.0
    b_m = a_m * aspect_b_over_a
    return a_m, b_m


def _superellipse_xz(
    a_m: float,
    b_m: float,
    theta: np.ndarray | float,
    z_center: float,
    exponent_p: float = 2.6,
) -> Tuple[np.ndarray | float, np.ndarray | float]:
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    x = a_m * np.sign(cos_t) * (np.abs(cos_t) ** (2.0 / exponent_p))
    z = z_center + b_m * np.sign(sin_t) * (np.abs(sin_t) ** (2.0 / exponent_p))
    return x, z


def _polyline_length_cm(pts: np.ndarray) -> float:
    """Computes polyline arc length in centimeters for an (N, 3) array in meters."""
    if len(pts) < 2:
        return 0.0
    return float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum()) * 100.0


def _polyline_length_2d_cm(pts_cm: np.ndarray) -> float:
    """Computes polyline arc length in centimeters for an (N, 2) array already in cm."""
    if len(pts_cm) < 2:
        return 0.0
    return float(np.linalg.norm(np.diff(pts_cm, axis=0), axis=1).sum())


def _resample_grid_mesh(
    grid_pts: np.ndarray,
    grid_uvs: np.ndarray,
    reverse_winding: bool = False,
) -> trimesh.Trimesh:
    """Builds a clean triangulated Trimesh from an (R, C, 3) structured grid."""
    nrows, ncols, _ = grid_pts.shape
    verts = grid_pts.reshape(-1, 3).astype(np.float32)
    uvs = grid_uvs.reshape(-1, 2).astype(np.float32)

    faces = []
    for r in range(nrows - 1):
        for c in range(ncols - 1):
            i0 = r * ncols + c
            i1 = r * ncols + (c + 1)
            i2 = (r + 1) * ncols + (c + 1)
            i3 = (r + 1) * ncols + c
            if not reverse_winding:
                faces.append([i0, i1, i2])
                faces.append([i0, i2, i3])
            else:
                faces.append([i0, i2, i1])
                faces.append([i0, i3, i2])

    mesh = trimesh.Trimesh(vertices=verts, faces=np.array(faces, dtype=np.int32), process=False)
    mesh.visual = TextureVisuals(uv=uvs)
    return mesh


def _scale_curve_2d_to_target_length(
    pts_cm: np.ndarray,
    target_len_cm: float,
    anchor_mode: str = "endpoints",
) -> np.ndarray:
    """
    Adjusts a 2D curve's middle control bulge along perpendicular axis so its arc length
    matches a target 2D seam length while preserving its fixed endpoints.
    """
    if anchor_mode != "endpoints" or len(pts_cm) < 3:
        return pts_cm
    p0, p1 = pts_cm[0], pts_cm[-1]
    chord = p1 - p0
    chord_len = float(np.linalg.norm(chord))
    if target_len_cm <= chord_len + 1e-4:
        return pts_cm
    # Project deviation from chord and scale perpendicular component
    t = np.linspace(0.0, 1.0, len(pts_cm))[:, None]
    base_line = p0 + t * chord
    dev = pts_cm - base_line
    lo, hi = 0.1, 8.0
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        cand = base_line + mid * dev
        if _polyline_length_2d_cm(cand) < target_len_cm:
            lo = mid
        else:
            hi = mid
    return base_line + (0.5 * (lo + hi)) * dev


def _compute_cut_line_2d(outline_cm: List[List[float]], seam_allowance_cm: float) -> List[List[float]]:
    """Computes an explicit outer cutting contour offset outward by seam_allowance_cm via mitred buffer."""
    poly = ShapelyPolygon(outline_cm)
    if not poly.is_valid:
        poly = poly.buffer(0.0)
    buffered = poly.buffer(float(seam_allowance_cm), join_style=2, mitre_limit=3.0)
    coords = list(buffered.exterior.coords)[:-1]
    return [[round(float(x), 3), round(float(y), 3)] for x, y in coords]


def export_panel_svg(panel_2d: Dict[str, Any], out_svg_path: str) -> None:
    """Exports an inspectable, true-scale (cm) SVG distinguishing stitch line, outer SA cut line, notches, grainline, and dimensions."""
    stitch_pts = np.array(panel_2d["outline_2d_cm"], dtype=np.float64)
    cut_pts_raw = panel_2d.get("cut_line_2d_cm") or _compute_cut_line_2d(panel_2d["outline_2d_cm"], panel_2d.get("seam_allowance_cm", 1.0))
    cut_pts = np.array(cut_pts_raw, dtype=np.float64)

    all_pts = np.vstack([stitch_pts, cut_pts])
    xmin, ymin = all_pts.min(axis=0)
    xmax, ymax = all_pts.max(axis=0)
    pad = 8.5  # generous cm margin so outer cut line + edge dimension labels stay strictly inside viewBox
    header_px = 52.0
    footer_px = 56.0
    scale = 10.0  # 10 px per cm
    w_px = ((xmax - xmin) + 2.0 * pad) * scale
    h_px = ((ymax - ymin) + 2.0 * pad) * scale + header_px + footer_px

    def to_svg(pt):
        return (pt[0] - xmin + pad) * scale, header_px + (ymax - pt[1] + pad) * scale

    stitch_center = stitch_pts.mean(axis=0)
    cut_str = " ".join(f"{to_svg(p)[0]:.2f},{to_svg(p)[1]:.2f}" for p in cut_pts)
    stitch_str = " ".join(f"{to_svg(p)[0]:.2f},{to_svg(p)[1]:.2f}" for p in stitch_pts)
    sa_cm = float(panel_2d.get("seam_allowance_cm", 1.0))
    sz_lbl = panel_2d.get("size_label", "M")

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_px:.1f}" height="{h_px:.1f}" viewBox="0 0 {w_px:.1f} {h_px:.1f}">',
        '  <rect width="100%" height="100%" fill="#fdfbf7"/>',
        f'  <text x="16" y="22" font-family="sans-serif" font-size="13" font-weight="bold" fill="#0f172a">SIZE {sz_lbl} · {panel_2d["panel_id"]} — {panel_2d["name"]}</text>',
        f'  <text x="16" y="38" font-family="sans-serif" font-size="10" fill="#475569">Units: cm | Seam Allowance: {sa_cm:.1f} cm | Algorithmic 2D CAD Spec With Cutline (Verify Before Plotter Cutting)</text>',
        f'  <polygon points="{cut_str}" fill="none" stroke="#1e293b" stroke-width="1.4" stroke-dasharray="6,3"/>',
        f'  <polygon points="{stitch_str}" fill="#fce7f3" fill-opacity="0.65" stroke="#be185d" stroke-width="2.0"/>',
    ]

    # Highlight open/finished boundaries separately from internal sewing seams
    for eid, edata in panel_2d.get("edges", {}).items():
        if edata.get("role") == "open_boundary":
            ec = np.array(edata["coordinates_cm"], dtype=np.float64)
            open_pts = " ".join(f"{to_svg(p)[0]:.2f},{to_svg(p)[1]:.2f}" for p in ec)
            lines.append(f'  <polyline points="{open_pts}" fill="none" stroke="#0284c7" stroke-width="2.6"/>')

    # Grainline with end ticks
    g = panel_2d.get("grainline")
    if g:
        gx0, gy0 = to_svg(g["start_cm"])
        gx1, gy1 = to_svg(g["end_cm"])
        lines.append(f'  <line x1="{gx0:.2f}" y1="{gy0:.2f}" x2="{gx1:.2f}" y2="{gy1:.2f}" stroke="#475569" stroke-width="1.5" stroke-dasharray="6,4"/>')
        lines.append(f'  <text x="{(gx0+gx1)*0.5:.1f}" y="{(gy0+gy1)*0.5 - 6:.1f}" font-family="sans-serif" font-size="9" fill="#475569" text-anchor="middle">GRAIN ({g.get("direction", "warp")})</text>')

    # Edge dimension labels offset outward away from panel centroid so labels stay clear of stitch & cut lines
    for eid, edata in panel_2d.get("edges", {}).items():
        ec = np.array(edata["coordinates_cm"], dtype=np.float64)
        mid = ec[len(ec) // 2]
        outward = mid - stitch_center
        norm = float(np.linalg.norm(outward))
        n_dir = (outward / norm) if norm > 1e-6 else np.array([0.0, 1.0])
        lbl_pt = mid + n_dir * (sa_cm + 2.2)
        lx, ly = to_svg(lbl_pt)
        lx = max(72.0, min(w_px - 72.0, lx))
        ly = max(header_px + 14.0, min(h_px - footer_px - 10.0, ly))
        lines.append(f'  <text x="{lx:.1f}" y="{ly:.1f}" font-family="monospace" font-size="8.5" fill="#0f172a" text-anchor="middle">{eid} ({edata["length_cm"]:.2f}cm)</text>')

    # Notches
    for notch in panel_2d.get("notches", []):
        nx, ny = to_svg(notch["position_cm"])
        lines.append(f'  <circle cx="{nx:.2f}" cy="{ny:.2f}" r="3.5" fill="#10b981" stroke="#064e3b" stroke-width="1"/>')

    # Pocket topstitch attachment path overlay if present on front torso
    if panel_2d.get("surface_attachments"):
        for att in panel_2d["surface_attachments"]:
            apts = " ".join(f"{to_svg(p)[0]:.2f},{to_svg(p)[1]:.2f}" for p in att["path_2d_cm"])
            lines.append(f'  <polyline points="{apts}" fill="none" stroke="#2563eb" stroke-width="2" stroke-dasharray="4,3"/>')

    # Bottom Legend inside canvas margin
    ly_leg = h_px - 32.0
    ly_leg2 = h_px - 14.0
    lines.extend([
        f'  <line x1="16" y1="{ly_leg:.1f}" x2="38" y2="{ly_leg:.1f}" stroke="#be185d" stroke-width="2.0"/>',
        f'  <text x="44" y="{ly_leg + 3:.1f}" font-family="sans-serif" font-size="9.5" fill="#0f172a">Stitch Line</text>',
        f'  <line x1="115" y1="{ly_leg:.1f}" x2="137" y2="{ly_leg:.1f}" stroke="#1e293b" stroke-width="1.4" stroke-dasharray="6,3"/>',
        f'  <text x="143" y="{ly_leg + 3:.1f}" font-family="sans-serif" font-size="9.5" fill="#0f172a">Cut Line (+{sa_cm:.1f} cm SA)</text>',
        f'  <line x1="262" y1="{ly_leg:.1f}" x2="284" y2="{ly_leg:.1f}" stroke="#0284c7" stroke-width="2.6"/>',
        f'  <text x="290" y="{ly_leg + 3:.1f}" font-family="sans-serif" font-size="9.5" fill="#0f172a">Open Boundary</text>',
        f'  <circle cx="22" cy="{ly_leg2 - 3:.1f}" r="3.5" fill="#10b981" stroke="#064e3b" stroke-width="1"/>',
        f'  <text x="32" y="{ly_leg2:.1f}" font-family="sans-serif" font-size="9.5" fill="#0f172a">Notch</text>',
        f'  <line x1="82" y1="{ly_leg2 - 3:.1f}" x2="104" y2="{ly_leg2 - 3:.1f}" stroke="#475569" stroke-width="1.5" stroke-dasharray="6,4"/>',
        f'  <text x="110" y="{ly_leg2:.1f}" font-family="sans-serif" font-size="9.5" fill="#0f172a">Grainline</text>',
        f'  <line x1="172" y1="{ly_leg2 - 3:.1f}" x2="194" y2="{ly_leg2 - 3:.1f}" stroke="#2563eb" stroke-width="2" stroke-dasharray="4,3"/>',
        f'  <text x="200" y="{ly_leg2:.1f}" font-family="sans-serif" font-size="9.5" fill="#0f172a">Topstitch Attachment</text>',
    ])
    lines.append("</svg>")

    os.makedirs(os.path.dirname(out_svg_path), exist_ok=True)
    with open(out_svg_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


class PatternGarmentBuilder:
    """
    Pattern-first 2D-to-3D builder for WearWise boxy drop-shoulder crew tees.
    """

    @classmethod
    def build_garment(
        cls,
        measurements: Dict[str, Any],
        size_label: str = "M",
        texture_atlas_path: Optional[str] = None,
        out_glb: Optional[str] = None,
        panels_svg_dir: Optional[str] = None,
        collar_type: str = "ribbed_crewneck",
        pocket_width_cm: Optional[float] = None,
        pocket_height_cm: Optional[float] = None,
        fabric_profile: Optional[Dict[str, Any]] = None,
        sku: str = "TSH-WW-CREW-001",
    ) -> Dict[str, Any]:
        half_chest_cm = float(measurements.get("half_chest_width_cm", 54.0))
        back_length_cm = float(measurements.get("back_length_cm", 67.0))
        shoulder_breadth_cm = float(measurements.get("shoulder_breadth_cm", 50.0))
        sleeve_length_cm = float(measurements.get("sleeve_length_cm", 17.0))
        sleeve_opening_cm = float(measurements.get("sleeve_opening_cm", 20.5))
        armhole_depth_cm = float(measurements.get("armhole_depth_cm", 26.5))
        collar_circ_cm = float(measurements.get("collar_circumference_cm", 44.0))
        hem_width_cm = float(measurements.get("hem_width_cm", 53.0))

        roughness = 0.62
        mat_name = f"WearWise_WaffleKnit_{size_label}"
        if fabric_profile:
            struct_l = str(fabric_profile.get("structure", "")).lower()
            if "linen" in struct_l or "woven" in struct_l:
                roughness = 0.78
            elif "fleece" in struct_l:
                roughness = 0.85
            elif "interlock" in struct_l:
                roughness = 0.54
            elif "jersey" in struct_l:
                roughness = 0.58
            f_id = str(fabric_profile.get("preset_id") or fabric_profile.get("id") or "custom")
            if f_id != "cotton_waffle_knit_240gsm":
                mat_name = f"WearWise_{f_id}_{size_label}"

        atlas_img = cls._load_or_create_atlas(texture_atlas_path)
        material = PBRMaterial(
            name=mat_name,
            baseColorTexture=atlas_img,
            baseColorFactor=[1.0, 1.0, 1.0, 1.0],
            metallicFactor=0.05,
            roughnessFactor=roughness,
            doubleSided=True,
        )

        # Shared graded 3D assembly coordinates (meters, Y-up; M matches Rev2 canonical exactly)
        y_hps = ANNY_UPRIGHT_FIT_FRAME["y_hps"]
        y_hem_bottom = y_hps - (back_length_cm / 100.0)
        hem_band_h = 0.028
        y_hem_seam = y_hem_bottom + hem_band_h
        y_underarm = ANNY_UPRIGHT_FIT_FRAME["y_underarm"] - (armhole_depth_cm - 26.5) / 100.0
        y_drop_sh = ANNY_UPRIGHT_FIT_FRAME["y_drop_sh"] - 0.45 * ((shoulder_breadth_cm - 50.0) / 200.0)
        z_center = ANNY_UPRIGHT_FIT_FRAME["z_center"]

        chest_aspect = 0.74 if half_chest_cm < 53.0 else 0.68
        a_chest, b_chest = _solve_superellipse_axes(half_chest_cm, aspect_b_over_a=chest_aspect, exponent_p=2.6)
        hem_aspect = 0.645 if hem_width_cm < 51.0 else 0.68
        hem_p = 2.8 if hem_width_cm < 51.0 else 2.6
        a_hem, b_hem = _solve_superellipse_axes(hem_width_cm, aspect_b_over_a=hem_aspect, exponent_p=hem_p)

        hem_shift_z = 0.015 if half_chest_cm < 53.0 else 0.030

        def torso_z_center(y_val: float) -> float:
            if y_val >= 1.05:
                return z_center
            t_g = np.exp(-((y_val - 0.80) / 0.14) ** 2)
            return float(z_center - hem_shift_z * t_g)

        neck_scale = collar_circ_cm / 44.0
        x_neck = 0.074 * neck_scale
        x_drop = shoulder_breadth_cm / 200.0
        front_neck_dip = 0.075 * neck_scale
        back_neck_dip = 0.025 * neck_scale
        r_z_neck_back = 0.070 * neck_scale
        r_z_neck_front = 0.070 * 1.18 * neck_scale
        r_z_arm = 0.082

        nu = 32
        nv_lower = 18
        nv_upper = 14
        i_neck_r = 8
        i_neck_l = 24

        ts_fine = np.linspace(np.pi, 0.0, 2000)
        xs_f, zs_f = _superellipse_xz(a_chest, b_chest, ts_fine, z_center)
        ds = np.linalg.norm(np.diff(np.column_stack([xs_f, zs_f]), axis=0), axis=1)
        cum_s = np.concatenate([[0.0], np.cumsum(ds)])
        cum_s /= cum_s[-1]
        u_lin = np.linspace(0.0, 1.0, nu + 1)
        theta_front_base = np.interp(u_lin, cum_s, ts_fine)
        theta_back_base = 2.0 * np.pi - theta_front_base

        # ---------------------------------------------------------------------
        # 1 & 2. FRONT & BACK TORSO 3D PANELS
        # ---------------------------------------------------------------------
        def build_torso_grid(is_front: bool):
            nrows = nv_lower + nv_upper + 1
            ncols = nu + 1
            pts = np.zeros((nrows, ncols, 3), dtype=np.float64)
            uvs = np.zeros((nrows, ncols, 2), dtype=np.float64)

            y_low_vals = np.linspace(y_hem_seam, y_underarm, nv_lower + 1)
            thetas = theta_front_base if is_front else theta_back_base
            for r, y in enumerate(y_low_vals):
                t_y = (y - y_hem_seam) / (y_underarm - y_hem_seam)
                a = a_hem + (a_chest - a_hem) * t_y
                b = b_hem + (b_chest - b_hem) * t_y
                p_y = hem_p + (2.6 - hem_p) * t_y
                zc_y = torso_z_center(y)
                for c, th in enumerate(thetas):
                    x, z = _superellipse_xz(a, b, th, zc_y, exponent_p=p_y)
                    pts[r, c] = [x, y, z]

            x_top = np.zeros(ncols)
            y_top = np.zeros(ncols)
            z_top = np.zeros(ncols)
            dip = front_neck_dip if is_front else back_neck_dip
            z_sign = 1.0 if is_front else -1.0
            r_z_neck = r_z_neck_front if is_front else r_z_neck_back
            for c in range(ncols):
                if c <= i_neck_r:
                    t = c / i_neck_r
                    x_top[c] = -x_drop + (x_drop - x_neck) * t
                    y_top[c] = y_drop_sh + (y_hps - y_drop_sh) * t
                    z_top[c] = z_center
                elif c >= i_neck_l:
                    t = (c - i_neck_l) / (nu - i_neck_l)
                    x_top[c] = x_neck + (x_drop - x_neck) * t
                    y_top[c] = y_hps + (y_drop_sh - y_hps) * t
                    z_top[c] = z_center
                else:
                    t = (c - i_neck_r) / (i_neck_l - i_neck_r)
                    ang = np.pi * (1.0 - t)
                    x_top[c] = x_neck * np.cos(ang)
                    y_top[c] = y_hps - dip * np.sin(ang)
                    z_top[c] = z_center + z_sign * r_z_neck * np.sin(ang)

            bot_row = pts[nv_lower].copy()
            for j in range(1, nv_upper + 1):
                r = nv_lower + j
                tv = j / nv_upper
                for c in range(ncols):
                    u_frac = c / nu
                    # Smooth C1 lateral window so axillary edges transition cleanly without pinching inward
                    u_taper = max(0.0, 1.0 - (abs(2.0 * u_frac - 1.0) ** 8))
                    x = bot_row[c, 0] + (x_top[c] - bot_row[c, 0]) * tv
                    y = bot_row[c, 1] + (y_top[c] - bot_row[c, 1]) * tv
                    z_arm_arc = z_center + z_sign * r_z_arm * np.sin(np.pi * tv)
                    z_lin = bot_row[c, 2] + (z_top[c] - bot_row[c, 2]) * tv
                    edge_w = abs(2.0 * u_frac - 1.0) ** 1.8
                    w_blend = min(1.0, 0.90 * edge_w * np.sin(np.pi * tv))
                    z = z_lin * (1.0 - w_blend) + z_arm_arc * w_blend
                    if c in (0, nu):
                        z = z_arm_arc
                    elif is_front:
                        # Smooth C1 front clavicle/chest dome (clears anterior chest & deltoids without mid-torso bulge)
                        if half_chest_cm < 53.0:
                            z += z_sign * 0.034 * (np.sin(np.pi * (tv ** 1.05)) ** 0.75) * u_taper
                        else:
                            z += z_sign * 0.028 * (np.sin(np.pi * (tv ** 1.4)) ** 0.8) * u_taper
                    else:
                        # Smooth C1 upper-biased scapula dome (clears rear scapulae cleanly without shelf)
                        z += z_sign * 0.042 * (np.sin(np.pi * (tv ** 1.6)) ** 0.8) * u_taper
                    pts[r, c] = [x, y, z]

            for r in range(nrows):
                for c in range(ncols):
                    u_frac = c / nu
                    u_tex = 0.05 + 0.60 * (u_frac if is_front else (1.0 - u_frac))
                    v_pil = 0.18 + 0.64 * np.clip((y_hps - pts[r, c, 1]) / (y_hps - y_hem_bottom), 0.0, 1.0)
                    uvs[r, c] = [u_tex, 1.0 - v_pil]

            return pts, uvs

        front_pts, front_uvs = build_torso_grid(is_front=True)
        back_pts, back_uvs = build_torso_grid(is_front=False)

        front_mesh = _resample_grid_mesh(front_pts, front_uvs, reverse_winding=False)
        back_mesh = _resample_grid_mesh(back_pts, back_uvs, reverse_winding=True)
        front_mesh.visual.material = material
        back_mesh.visual.material = material

        front_edges_3d = {
            "FRONT_BOTTOM_SEAM": front_pts[0, :, :],
            "FRONT_SIDE_R": front_pts[0 : nv_lower + 1, 0, :],
            "FRONT_SIDE_L": front_pts[0 : nv_lower + 1, -1, :],
            "FRONT_ARMHOLE_R": front_pts[nv_lower:, 0, :],
            "FRONT_ARMHOLE_L": front_pts[nv_lower:, -1, :],
            "FRONT_SHOULDER_R": front_pts[-1, 0 : i_neck_r + 1, :],
            "FRONT_SHOULDER_L": front_pts[-1, i_neck_l:, :],
            "FRONT_NECKLINE": front_pts[-1, i_neck_r : i_neck_l + 1, :],
        }
        back_edges_3d = {
            "BACK_BOTTOM_SEAM": back_pts[0, :, :],
            "BACK_SIDE_R": back_pts[0 : nv_lower + 1, 0, :],
            "BACK_SIDE_L": back_pts[0 : nv_lower + 1, -1, :],
            "BACK_ARMHOLE_R": back_pts[nv_lower:, 0, :],
            "BACK_ARMHOLE_L": back_pts[nv_lower:, -1, :],
            "BACK_SHOULDER_R": back_pts[-1, 0 : i_neck_r + 1, :],
            "BACK_SHOULDER_L": back_pts[-1, i_neck_l:, :],
            "BACK_NECKLINE": back_pts[-1, i_neck_r : i_neck_l + 1, :],
        }

        # ---------------------------------------------------------------------
        # 3 & 4. LEFT & RIGHT DROPPED SLEEVE 3D PANELS
        # ---------------------------------------------------------------------
        def build_sleeve_panel(is_left: bool):
            sign_x = 1.0 if is_left else -1.0
            col_idx = -1 if is_left else 0
            f_arm = front_pts[nv_lower:, col_idx, :]   # underarm -> drop_sh
            b_arm = back_pts[nv_lower:, col_idx, :]    # underarm -> drop_sh

            cap_loop = np.vstack([f_arm, b_arm[-2::-1]])
            n_cap = len(cap_loop)

            cuff_circ_m = (2.0 * sleeve_opening_cm) / 100.0
            cuff_radius_m = cuff_circ_m / (2.0 * np.pi)
            # Align A-pose sleeve axis with Anny's natural progressive forward elbow flexion (+Z) by reach
            dz_arm = 0.140 if sleeve_length_cm <= 15.5 else (0.190 if sleeve_length_cm <= 17.5 else 0.240)
            arm_dir = np.array([
                sign_x * 0.540,
                -0.815,
                dz_arm,
            ], dtype=np.float64)
            arm_dir /= np.linalg.norm(arm_dir)

            ref_up = np.array([0.0, 1.0, 0.0])
            e_top = ref_up - np.dot(ref_up, arm_dir) * arm_dir
            e_top /= np.linalg.norm(e_top)
            e_front = np.cross(arm_dir, e_top)
            e_front /= np.linalg.norm(e_front)
            if e_front[2] < 0:
                e_front = -e_front

            drop_sh_pt = f_arm[-1]
            underarm_pt = f_arm[0]
            armhole_mid = 0.5 * (drop_sh_pt + underarm_pt)
            sleeve_len_m = sleeve_length_cm / 100.0
            cuff_center = armhole_mid + arm_dir * sleeve_len_m

            angles = np.linspace(0.0, 2.0 * np.pi, n_cap)
            cuff_loop = np.zeros_like(cap_loop)
            for k, ang in enumerate(angles):
                cuff_loop[k] = cuff_center + cuff_radius_m * (-np.cos(ang) * e_top + np.sin(ang) * e_front)

            n_ax = 10
            cuff_band_frac = min(0.028 / sleeve_len_m, 0.25)
            s_vals = np.linspace(0.0, 1.0, n_ax + 1)
            seam_idx = n_ax - 2
            s_vals[: seam_idx + 1] = np.linspace(0.0, 1.0 - cuff_band_frac, seam_idx + 1)
            s_vals[seam_idx:] = np.linspace(1.0 - cuff_band_frac, 1.0, n_ax - seam_idx + 1)

            slv_pts = np.zeros((n_ax + 1, n_cap, 3), dtype=np.float64)
            slv_uvs = np.zeros((n_ax + 1, n_cap, 2), dtype=np.float64)
            for r, s in enumerate(s_vals):
                slv_pts[r] = (1.0 - s) * cap_loop + s * cuff_loop
                for c in range(n_cap):
                    u_frac = c / (n_cap - 1)
                    if r >= seam_idx:
                        t_c = (r - seam_idx) / max(n_ax - seam_idx, 1)
                        v_pil = 0.858 + 0.067 * t_c
                        slv_uvs[r, c] = [0.05 + 0.90 * u_frac, 1.0 - v_pil]
                    else:
                        t_b = r / max(seam_idx, 1)
                        v_pil = 0.22 + 0.43 * t_b
                        slv_uvs[r, c] = [0.05 + 0.60 * u_frac, 1.0 - v_pil]

            slv_mesh = _resample_grid_mesh(slv_pts, slv_uvs, reverse_winding=is_left)
            slv_mesh.visual.material = material

            edges_3d = {
                "SLEEVE_CAP_FRONT": slv_pts[0, : nv_upper + 1, :],
                "SLEEVE_CAP_BACK": slv_pts[0, nv_upper:, :][::-1],
                "SLEEVE_UNDERARM_F": slv_pts[:, 0, :],
                "SLEEVE_UNDERARM_B": slv_pts[:, -1, :],
                "SLEEVE_CUFF_OPENING": slv_pts[-1, :, :],
            }
            return slv_mesh, edges_3d

        sleeve_l_mesh, sleeve_l_edges = build_sleeve_panel(is_left=True)
        sleeve_r_mesh, sleeve_r_edges = build_sleeve_panel(is_left=False)

        # ---------------------------------------------------------------------
        # 5. RIBBED CREWNECK COLLAR BAND (PANEL-COLLAR-RIB)
        # ---------------------------------------------------------------------
        f_neck = front_pts[-1, i_neck_r : i_neck_l + 1, :]
        b_neck = back_pts[-1, i_neck_r : i_neck_l + 1, :]
        neck_seam_loop = np.vstack([f_neck, b_neck[-2::-1]])
        n_neck = len(neck_seam_loop)

        neck_center = neck_seam_loop[:-1].mean(axis=0)
        collar_h = 0.038 if collar_type == "mock_neck" else (0.022 if collar_type == "wide_crew" else 0.028)
        raw_top_loop = neck_seam_loop + np.array([0.0, collar_h, 0.0])
        horiz_offsets = raw_top_loop[:, [0, 2]] - neck_center[[0, 2]]
        lo, hi = 0.50, 1.20
        for _ in range(30):
            mid = 0.5 * (lo + hi)
            cand = raw_top_loop.copy()
            cand[:, 0] = neck_center[0] + mid * horiz_offsets[:, 0]
            cand[:, 2] = neck_center[2] + mid * horiz_offsets[:, 1]
            if _polyline_length_cm(cand) > collar_circ_cm:
                hi = mid
            else:
                lo = mid
        s_col = 0.5 * (lo + hi)
        collar_top_loop = raw_top_loop.copy()
        collar_top_loop[:, 0] = neck_center[0] + s_col * horiz_offsets[:, 0]
        collar_top_loop[:, 2] = neck_center[2] + s_col * horiz_offsets[:, 1]

        n_col_rows = 4
        col_pts = np.zeros((n_col_rows + 1, n_neck, 3), dtype=np.float64)
        col_uvs = np.zeros((n_col_rows + 1, n_neck, 2), dtype=np.float64)
        for r in range(n_col_rows + 1):
            t_r = r / n_col_rows
            col_pts[r] = (1.0 - t_r) * neck_seam_loop + t_r * collar_top_loop
            for c in range(n_neck):
                v_pil = 0.105 - 0.090 * t_r
                col_uvs[r, c] = [0.02 + 0.96 * (c / (n_neck - 1)), 1.0 - v_pil]

        collar_mesh = _resample_grid_mesh(col_pts, col_uvs, reverse_winding=False)
        collar_mesh.visual.material = material
        collar_edges_3d = {
            "COLLAR_NECK_SEAM_FRONT": col_pts[0, : (i_neck_l - i_neck_r + 1), :],
            "COLLAR_NECK_SEAM_BACK": col_pts[0, (i_neck_l - i_neck_r) :, :][::-1],
            "COLLAR_TOP_OPENING": col_pts[-1, :, :],
            "COLLAR_JOIN_START": col_pts[:, 0, :],
            "COLLAR_JOIN_END": col_pts[:, -1, :],
        }

        # ---------------------------------------------------------------------
        # 6. BOTTOM HEM BAND (PANEL-HEM-BAND)
        # ---------------------------------------------------------------------
        front_hem_row = front_pts[0, :, :]
        back_hem_row = back_pts[0, :, :]
        hem_seam_loop = np.vstack([front_hem_row, back_hem_row[-2::-1]])
        n_hem = len(hem_seam_loop)

        n_hem_rows = 3
        hem_pts = np.zeros((n_hem_rows + 1, n_hem, 3), dtype=np.float64)
        hem_uvs = np.zeros((n_hem_rows + 1, n_hem, 2), dtype=np.float64)
        for r in range(n_hem_rows + 1):
            t_r = r / n_hem_rows
            hem_pts[r] = hem_seam_loop - np.array([0.0, hem_band_h * t_r, 0.0])
            for c in range(n_hem):
                v_pil = 0.935 + 0.060 * t_r
                hem_uvs[r, c] = [0.02 + 0.96 * (c / (n_hem - 1)), 1.0 - v_pil]

        hem_mesh = _resample_grid_mesh(hem_pts, hem_uvs, reverse_winding=True)
        hem_mesh.visual.material = material
        hem_edges_3d = {
            "HEM_BODY_SEAM_FRONT": hem_pts[0, : nu + 1, :],
            "HEM_BODY_SEAM_BACK": hem_pts[0, nu:, :][::-1],
            "HEM_LOWER_OPENING": hem_pts[-1, :, :],
            "HEM_JOIN_START": hem_pts[:, 0, :],
            "HEM_JOIN_END": hem_pts[:, -1, :],
        }

        # ---------------------------------------------------------------------
        # 7. LEFT CHEST PATCH POCKET (PANEL-POCKET-CHEST — GRADED)
        # ---------------------------------------------------------------------
        base_pkt_w = float(pocket_width_cm) if pocket_width_cm is not None else 11.5
        base_pkt_h = float(pocket_height_cm) if pocket_height_cm is not None else 13.5
        pkt_w_cm = round(base_pkt_w + 0.5 * ((half_chest_cm - 54.0) / 4.0), 2)
        pkt_h_cm = round(base_pkt_h + 0.5 * ((back_length_cm - 67.0) / 3.0), 2)
        pkt_x_min = round(0.045 * (half_chest_cm / 54.0), 4)
        pkt_x_max = pkt_x_min + pkt_w_cm / 100.0
        pkt_y_min = round(y_hps - 0.245 * (back_length_cm / 67.0), 4)
        pkt_y_max = pkt_y_min + pkt_h_cm / 100.0

        f_flat = front_pts.reshape(-1, 3)
        front_z_interp = LinearNDInterpolator(f_flat[:, :2], f_flat[:, 2])

        nx_p, ny_p = 10, 12
        pkt_pts = np.zeros((ny_p + 1, nx_p + 1, 3), dtype=np.float64)
        pkt_uvs = np.zeros((ny_p + 1, nx_p + 1, 2), dtype=np.float64)
        for r in range(ny_p + 1):
            tv = r / ny_p
            y = pkt_y_min + (pkt_y_max - pkt_y_min) * tv
            for c in range(nx_p + 1):
                tu = c / nx_p
                x = pkt_x_min + (pkt_x_max - pkt_x_min) * tu
                if r == 0 and c in (0, nx_p):
                    y_eff = y + 0.010
                    x_eff = x + (0.010 if c == 0 else -0.010)
                else:
                    y_eff, x_eff = y, x
                z_val = front_z_interp(x_eff, y_eff)
                if np.isnan(z_val):
                    z_val = float(z_center + b_chest * 0.85)
                is_rim = (r == 0 or r == ny_p or c == 0 or c == nx_p)
                z_offset = 0.0035 if is_rim else 0.0055
                pkt_pts[r, c] = [x_eff, y_eff, float(z_val) + z_offset]
                v_pil = 0.414 - 0.266 * tv
                pkt_uvs[r, c] = [0.684 + 0.268 * tu, 1.0 - v_pil]

        pocket_mesh = _resample_grid_mesh(pkt_pts, pkt_uvs, reverse_winding=False)
        pocket_mesh.visual.material = material
        pocket_edges_3d = {
            "POCKET_TOP_HEM": pkt_pts[-1, :, :],
            "POCKET_BOTTOM": pkt_pts[0, :, :],
            "POCKET_SIDE_L": pkt_pts[:, -1, :],
            "POCKET_SIDE_R": pkt_pts[:, 0, :],
        }

        # ---------------------------------------------------------------------
        # ASSEMBLE 7-COMPONENT GLB SCENE
        # ---------------------------------------------------------------------
        components = {
            "PANEL-FRONT-TORSO": front_mesh,
            "PANEL-BACK-TORSO": back_mesh,
            "PANEL-SLEEVE-L": sleeve_l_mesh,
            "PANEL-SLEEVE-R": sleeve_r_mesh,
            "PANEL-COLLAR-RIB": collar_mesh,
            "PANEL-HEM-BAND": hem_mesh,
            "PANEL-POCKET-CHEST": pocket_mesh,
        }
        scene = trimesh.Scene()
        if fabric_profile:
            scene.metadata["wearwise_fabric_profile"] = {
                "preset_id": fabric_profile.get("preset_id") or fabric_profile.get("id"),
                "name": fabric_profile.get("name"),
                "composition": fabric_profile.get("composition"),
                "gsm": fabric_profile.get("gsm"),
                "provisional": bool(fabric_profile.get("provisional", True)),
            }
        for panel_id, pmesh in components.items():
            scene.add_geometry(pmesh, node_name=panel_id, geom_name=panel_id)

        if out_glb:
            os.makedirs(os.path.dirname(out_glb), exist_ok=True)
            scene.export(out_glb, file_type="glb")

        # ---------------------------------------------------------------------
        # AUTHORITATIVE 2D PATTERN OUTLINES (ALL 7 PANELS, UNITS: CM)
        # ---------------------------------------------------------------------
        panel_2d_specs = cls._build_authoritative_2d_panels(
            size_label=size_label,
            half_chest_cm=half_chest_cm,
            back_length_cm=back_length_cm,
            shoulder_breadth_cm=shoulder_breadth_cm,
            sleeve_length_cm=sleeve_length_cm,
            sleeve_opening_cm=sleeve_opening_cm,
            collar_circ_cm=collar_circ_cm,
            hem_width_cm=hem_width_cm,
            pkt_w_cm=pkt_w_cm,
            pkt_h_cm=pkt_h_cm,
            pkt_x_min=pkt_x_min,
            pkt_y_min=pkt_y_min,
            x_neck_cm=round(x_neck * 100.0, 3),
            front_neck_dip_cm=round(front_neck_dip * 100.0, 3),
            back_neck_dip_cm=round(back_neck_dip * 100.0, 3),
            y_underarm=y_underarm,
            y_drop_sh=y_drop_sh,
            front_edges_3d=front_edges_3d,
            back_edges_3d=back_edges_3d,
            sleeve_l_edges_3d=sleeve_l_edges,
            collar_edges_3d=collar_edges_3d,
            hem_edges_3d=hem_edges_3d,
            pocket_edges_3d=pocket_edges_3d,
            components=components,
            y_hem_seam=y_hem_seam,
            collar_h_cm=round(collar_h * 100.0, 2),
        )

        if panels_svg_dir:
            for p_spec in panel_2d_specs:
                export_panel_svg(p_spec, os.path.join(panels_svg_dir, f"{p_spec['panel_id']}.svg"))

        # Lookup helper for 2D edge lengths
        p2d_by_id = {p["panel_id"]: p for p in panel_2d_specs}

        # ---------------------------------------------------------------------
        # EXPLICIT 1-TO-1 SEAM-EDGE CONTRACT + COLLAR & POCKET CONTRACTS
        # ---------------------------------------------------------------------
        def make_ordinary_seam(
            seam_id: str,
            name: str,
            seam_type: str,
            src_panel: str,
            src_edge: str,
            src_pts_3d: np.ndarray,
            dst_panel: str,
            dst_edge: str,
            dst_pts_3d: np.ndarray,
            notches: List[str],
            extra_fields: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            src_2d_len = p2d_by_id[src_panel]["edges"][src_edge]["length_cm"]
            dst_2d_len = p2d_by_id[dst_panel]["edges"][dst_edge]["length_cm"]
            src_3d_len = _polyline_length_cm(src_pts_3d)
            dst_3d_len = _polyline_length_cm(dst_pts_3d)

            if len(src_pts_3d) == len(dst_pts_3d):
                gap_fwd = float(np.linalg.norm(src_pts_3d - dst_pts_3d, axis=1).max()) * 1000.0
                gap_rev = float(np.linalg.norm(src_pts_3d - dst_pts_3d[::-1], axis=1).max()) * 1000.0
                gap_mm = min(gap_fwd, gap_rev)
            else:
                gap_mm = 999.0

            compat_2d = abs(src_2d_len - dst_2d_len) <= 0.25
            compat_3d = (abs(src_3d_len - dst_3d_len) <= 0.25) and (gap_mm <= 0.5)
            rec = {
                "seam_id": seam_id,
                "name": name,
                "record_kind": "ordinary_sewing_seam",
                "seam_type": seam_type,
                "source_panel_id": src_panel,
                "source_edge_id": src_edge,
                "dest_panel_id": dst_panel,
                "dest_edge_id": dst_edge,
                "expected_edge_length_cm": round(src_2d_len, 2),
                "actual_2d_source_length_cm": round(src_2d_len, 2),
                "actual_2d_dest_length_cm": round(dst_2d_len, 2),
                "actual_3d_source_length_cm": round(src_3d_len, 2),
                "actual_3d_dest_length_cm": round(dst_3d_len, 2),
                "length_delta_2d_cm": round(abs(src_2d_len - dst_2d_len), 3),
                "length_delta_3d_cm": round(abs(src_3d_len - dst_3d_len), 3),
                "max_3d_vertex_gap_mm": round(gap_mm, 4),
                "compatible": bool(compat_2d and compat_3d),
                "notches": notches,
            }
            if extra_fields:
                rec.update(extra_fields)
            return rec

        # Independent collar closure transformation contract (distinguishes cutline, 2D stitch slant, and 3D frustum meridian)
        col_seam_2d_tot = (
            p2d_by_id["PANEL-COLLAR-RIB"]["edges"]["COLLAR_NECK_SEAM_FRONT"]["length_cm"]
            + p2d_by_id["PANEL-COLLAR-RIB"]["edges"]["COLLAR_NECK_SEAM_BACK"]["length_cm"]
        )
        col_sa_cm = float(p2d_by_id["PANEL-COLLAR-RIB"]["seam_allowance_cm"])
        col_h_cm = round(collar_h * 100.0, 2)
        col_half_dx = 0.5 * (col_seam_2d_tot - collar_circ_cm)
        col_exp_2d_slant = round(math.hypot(col_half_dx, col_h_cm), 2)
        col_cut_len = round(math.hypot(col_half_dx, col_h_cm + 2.0 * col_sa_cm), 2)
        col_radial_taper_cm = float(np.linalg.norm((1.0 - s_col) * horiz_offsets[0])) * 100.0
        col_exp_3d_meridian = round(math.hypot(col_h_cm, col_radial_taper_cm), 2)
        collar_closure_contract = {
            "cause": "conical_ring_curvature_development",
            "explanation": (
                "The 2D pattern drafts the tapered collar band on a straight strip (end slant combines vertical band height "
                f"{col_h_cm:.2f} cm and half circumferential taper {col_half_dx:.2f} cm -> {col_exp_2d_slant:.2f} cm), "
                "whereas closing the ring into a 3D conical collar distributes the circumference reduction radially "
                f"(join radial taper {col_radial_taper_cm:.2f} cm -> 3D seam meridian {col_exp_3d_meridian:.2f} cm). "
                f"Cutting edge adds 2 x {col_sa_cm:.1f} cm seam allowance ({col_cut_len:.2f} cm)."
            ),
            "measurement_convention": "2D cutting_edge > 2D stitch_slant > 3D ring_meridian; values are NOT artificially forced equal.",
            "band_height_cm": col_h_cm,
            "seam_allowance_cm": col_sa_cm,
            "cutting_edge_length_cm": col_cut_len,
            "expected_2d_stitch_slant_cm": col_exp_2d_slant,
            "radial_shrink_factor_xz": round(float(s_col), 4),
            "radial_taper_at_join_cm": round(col_radial_taper_cm, 3),
            "expected_3d_meridian_cm": col_exp_3d_meridian,
            "tolerance_cm": 0.25,
        }

        seam_map = [
            make_ordinary_seam(
                "SEAM-SH-L", "Left Shoulder Seam", "flat_joined",
                "PANEL-FRONT-TORSO", "FRONT_SHOULDER_L", front_edges_3d["FRONT_SHOULDER_L"],
                "PANEL-BACK-TORSO", "BACK_SHOULDER_L", back_edges_3d["BACK_SHOULDER_L"],
                ["neck_hps_l", "drop_shoulder_l"],
            ),
            make_ordinary_seam(
                "SEAM-SH-R", "Right Shoulder Seam", "flat_joined",
                "PANEL-FRONT-TORSO", "FRONT_SHOULDER_R", front_edges_3d["FRONT_SHOULDER_R"],
                "PANEL-BACK-TORSO", "BACK_SHOULDER_R", back_edges_3d["BACK_SHOULDER_R"],
                ["neck_hps_r", "drop_shoulder_r"],
            ),
            make_ordinary_seam(
                "SEAM-SIDE-L", "Left Torso Side Seam", "closed_edge",
                "PANEL-FRONT-TORSO", "FRONT_SIDE_L", front_edges_3d["FRONT_SIDE_L"],
                "PANEL-BACK-TORSO", "BACK_SIDE_L", back_edges_3d["BACK_SIDE_L"],
                ["underarm_l", "hem_seam_l"],
            ),
            make_ordinary_seam(
                "SEAM-SIDE-R", "Right Torso Side Seam", "closed_edge",
                "PANEL-FRONT-TORSO", "FRONT_SIDE_R", front_edges_3d["FRONT_SIDE_R"],
                "PANEL-BACK-TORSO", "BACK_SIDE_R", back_edges_3d["BACK_SIDE_R"],
                ["underarm_r", "hem_seam_r"],
            ),
            make_ordinary_seam(
                "SEAM-ARMHOLE-L-FRONT", "Left Armhole Front Inset Seam", "curved_inset",
                "PANEL-FRONT-TORSO", "FRONT_ARMHOLE_L", front_edges_3d["FRONT_ARMHOLE_L"],
                "PANEL-SLEEVE-L", "SLEEVE_CAP_FRONT", sleeve_l_edges["SLEEVE_CAP_FRONT"],
                ["underarm_l", "shoulder_apex_l"],
            ),
            make_ordinary_seam(
                "SEAM-ARMHOLE-L-BACK", "Left Armhole Back Inset Seam", "curved_inset",
                "PANEL-BACK-TORSO", "BACK_ARMHOLE_L", back_edges_3d["BACK_ARMHOLE_L"],
                "PANEL-SLEEVE-L", "SLEEVE_CAP_BACK", sleeve_l_edges["SLEEVE_CAP_BACK"],
                ["underarm_l", "shoulder_apex_l"],
            ),
            make_ordinary_seam(
                "SEAM-ARMHOLE-R-FRONT", "Right Armhole Front Inset Seam", "curved_inset",
                "PANEL-FRONT-TORSO", "FRONT_ARMHOLE_R", front_edges_3d["FRONT_ARMHOLE_R"],
                "PANEL-SLEEVE-R", "SLEEVE_CAP_FRONT", sleeve_r_edges["SLEEVE_CAP_FRONT"],
                ["underarm_r", "shoulder_apex_r"],
            ),
            make_ordinary_seam(
                "SEAM-ARMHOLE-R-BACK", "Right Armhole Back Inset Seam", "curved_inset",
                "PANEL-BACK-TORSO", "BACK_ARMHOLE_R", back_edges_3d["BACK_ARMHOLE_R"],
                "PANEL-SLEEVE-R", "SLEEVE_CAP_BACK", sleeve_r_edges["SLEEVE_CAP_BACK"],
                ["underarm_r", "shoulder_apex_r"],
            ),
            make_ordinary_seam(
                "SEAM-UNDERARM-L", "Left Sleeve Underarm Seam", "tubular_closed",
                "PANEL-SLEEVE-L", "SLEEVE_UNDERARM_F", sleeve_l_edges["SLEEVE_UNDERARM_F"],
                "PANEL-SLEEVE-L", "SLEEVE_UNDERARM_B", sleeve_l_edges["SLEEVE_UNDERARM_B"],
                ["underarm_l", "cuff_underarm_l"],
            ),
            make_ordinary_seam(
                "SEAM-UNDERARM-R", "Right Sleeve Underarm Seam", "tubular_closed",
                "PANEL-SLEEVE-R", "SLEEVE_UNDERARM_F", sleeve_r_edges["SLEEVE_UNDERARM_F"],
                "PANEL-SLEEVE-R", "SLEEVE_UNDERARM_B", sleeve_r_edges["SLEEVE_UNDERARM_B"],
                ["underarm_r", "cuff_underarm_r"],
            ),
            make_ordinary_seam(
                "SEAM-NECK-RIB-FRONT", "Collar Front Neckband Seam", "binding_rib",
                "PANEL-FRONT-TORSO", "FRONT_NECKLINE", front_edges_3d["FRONT_NECKLINE"],
                "PANEL-COLLAR-RIB", "COLLAR_NECK_SEAM_FRONT", collar_edges_3d["COLLAR_NECK_SEAM_FRONT"],
                ["center_front_neck", "hps_l", "hps_r"],
            ),
            make_ordinary_seam(
                "SEAM-NECK-RIB-BACK", "Collar Back Neckband Seam", "binding_rib",
                "PANEL-BACK-TORSO", "BACK_NECKLINE", back_edges_3d["BACK_NECKLINE"],
                "PANEL-COLLAR-RIB", "COLLAR_NECK_SEAM_BACK", collar_edges_3d["COLLAR_NECK_SEAM_BACK"],
                ["center_back_neck", "hps_l", "hps_r"],
            ),
            make_ordinary_seam(
                "SEAM-COLLAR-JOIN", "Collar Rib Ring Closure Seam", "closed_edge",
                "PANEL-COLLAR-RIB", "COLLAR_JOIN_START", collar_edges_3d["COLLAR_JOIN_START"],
                "PANEL-COLLAR-RIB", "COLLAR_JOIN_END", collar_edges_3d["COLLAR_JOIN_END"],
                ["collar_join_r"],
                extra_fields={"transformation_contract": collar_closure_contract},
            ),
            make_ordinary_seam(
                "SEAM-HEM-BAND-FRONT", "Bottom Hem Band Front Binding", "binding_hem",
                "PANEL-FRONT-TORSO", "FRONT_BOTTOM_SEAM", front_edges_3d["FRONT_BOTTOM_SEAM"],
                "PANEL-HEM-BAND", "HEM_BODY_SEAM_FRONT", hem_edges_3d["HEM_BODY_SEAM_FRONT"],
                ["side_l_hem", "side_r_hem", "center_front_hem"],
            ),
            make_ordinary_seam(
                "SEAM-HEM-BAND-BACK", "Bottom Hem Band Back Binding", "binding_hem",
                "PANEL-BACK-TORSO", "BACK_BOTTOM_SEAM", back_edges_3d["BACK_BOTTOM_SEAM"],
                "PANEL-HEM-BAND", "HEM_BODY_SEAM_BACK", hem_edges_3d["HEM_BODY_SEAM_BACK"],
                ["side_l_hem", "side_r_hem", "center_back_hem"],
            ),
            make_ordinary_seam(
                "SEAM-HEM-JOIN", "Bottom Hem Band Ring Closure Seam", "closed_edge",
                "PANEL-HEM-BAND", "HEM_JOIN_START", hem_edges_3d["HEM_JOIN_START"],
                "PANEL-HEM-BAND", "HEM_JOIN_END", hem_edges_3d["HEM_JOIN_END"],
                ["hem_join_r"],
            ),
        ]

        # Explicit Surface Attachment Path & Surface-Projection Contract for Chest Patch Pocket
        pocket_stitch_3d = np.vstack([pkt_pts[::-1, 0, :], pkt_pts[0, 1:, :], pkt_pts[1:, -1, :]])
        pkt_att_2d = p2d_by_id["PANEL-FRONT-TORSO"]["surface_attachments"][0]
        pkt_2d_edges_len = (
            p2d_by_id["PANEL-POCKET-CHEST"]["edges"]["POCKET_SIDE_R"]["length_cm"]
            + p2d_by_id["PANEL-POCKET-CHEST"]["edges"]["POCKET_BOTTOM"]["length_cm"]
            + p2d_by_id["PANEL-POCKET-CHEST"]["edges"]["POCKET_SIDE_L"]["length_cm"]
        )
        pkt_3d_len = _polyline_length_cm(pocket_stitch_3d)

        # Compute independent 3D projection of the front-torso 2D path onto the curved torso shell + 3.5 mm relief
        p2d_pts = np.array(pkt_att_2d["path_2d_cm"], dtype=np.float64)
        dense_xy = []
        for idx_s in range(len(p2d_pts) - 1):
            a_pt, b_pt = p2d_pts[idx_s], p2d_pts[idx_s + 1]
            n_sub = max(int(round(np.linalg.norm(b_pt - a_pt) * 2)), 2)
            for k in range(n_sub):
                t_s = k / n_sub
                dense_xy.append(a_pt + (b_pt - a_pt) * t_s)
        dense_xy.append(p2d_pts[-1])
        dense_xy_arr = np.array(dense_xy, dtype=np.float64) / 100.0
        dense_y_m = dense_xy_arr[:, 1] + y_hem_seam
        dense_z_m = front_z_interp(dense_xy_arr[:, 0], dense_y_m)
        valid_z = ~np.isnan(dense_z_m)
        proj_path_3d = np.column_stack([dense_xy_arr[valid_z, 0], dense_y_m[valid_z], dense_z_m[valid_z] + 0.0035])
        expected_proj_3d_cm = _polyline_length_cm(proj_path_3d)

        rim_z_base = front_z_interp(pocket_stitch_3d[:, 0], pocket_stitch_3d[:, 1])
        rim_valid = ~np.isnan(rim_z_base)
        rim_reliefs_mm = (pocket_stitch_3d[rim_valid, 2] - rim_z_base[rim_valid]) * 1000.0
        mean_relief_mm = float(np.mean(rim_reliefs_mm)) if len(rim_reliefs_mm) else 0.0
        min_relief_mm = float(np.min(rim_reliefs_mm)) if len(rim_reliefs_mm) else 0.0
        max_relief_mm = float(np.max(rim_reliefs_mm)) if len(rim_reliefs_mm) else 0.0

        curvature_dev_cm = round(pkt_3d_len - pkt_2d_edges_len, 2)
        stretch_ratio = round(pkt_3d_len / max(pkt_2d_edges_len, 1e-6), 4)
        proj_err_cm = round(abs(pkt_3d_len - expected_proj_3d_cm), 2)
        pkt_compat = (
            abs(pkt_2d_edges_len - pkt_att_2d["path_length_2d_cm"]) <= 0.25
            and proj_err_cm <= 1.00
            and (1.00 <= stretch_ratio <= 1.12)
            and abs(mean_relief_mm - 3.5) <= 1.0
            and min_relief_mm > 0.5
        )

        surface_attachments = [
            {
                "attachment_id": "ATTACH-POCKET-CHEST",
                "name": "Chest Patch Pocket Topstitch Attachment",
                "record_kind": "surface_attachment_path",
                "attachment_type": "topstitched_applique_surface_path",
                "source_panel_id": "PANEL-POCKET-CHEST",
                "source_edge_ids": ["POCKET_SIDE_R", "POCKET_BOTTOM", "POCKET_SIDE_L"],
                "target_panel_id": "PANEL-FRONT-TORSO",
                "target_attachment_type": "interior_surface_path",
                "target_surface_path_2d_cm": pkt_att_2d["path_2d_cm"],
                "target_surface_path_3d_m": [[round(float(x), 4) for x in pt] for pt in pocket_stitch_3d],
                "intended_relief_mm": 3.5,
                "expected_path_length_cm": round(pkt_2d_edges_len, 2),
                "actual_2d_path_length_cm": round(pkt_att_2d["path_length_2d_cm"], 2),
                "expected_projected_3d_path_length_cm": round(expected_proj_3d_cm, 2),
                "actual_3d_path_length_cm": round(pkt_3d_len, 2),
                "curvature_deviation_cm": curvature_dev_cm,
                "curvature_stretch_ratio": stretch_ratio,
                "attachment_contract": {
                    "mapping_relationship": "planar_chest_box_to_curved_3d_torso_surface_with_normal_relief",
                    "deviation_explanation": (
                        f"Planar 2D pocket path ({pkt_2d_edges_len:.2f} cm) wraps onto convex front torso superellipse "
                        f"Z-curvature and shoulder slope, adding {curvature_dev_cm:+.2f} cm geodesic arc length "
                        f"({expected_proj_3d_cm:.2f} cm surface integral + beveled corner rim discretization = {pkt_3d_len:.2f} cm) "
                        "plus 3.5 mm normal relief."
                    ),
                    "measured_rim_relief_mm": {
                        "mean": round(mean_relief_mm, 3),
                        "min": round(min_relief_mm, 3),
                        "max": round(max_relief_mm, 3),
                    },
                    "tolerances": {
                        "tolerance_2d_cm": 0.25,
                        "tolerance_3d_projection_cm": 1.00,
                        "stretch_ratio_bounds": [1.00, 1.12],
                        "relief_target_mm": 3.5,
                        "relief_tolerance_mm": 1.0,
                    },
                },
                "compatible": bool(pkt_compat),
                "notches": ["pocket_top_left", "pocket_top_right"],
            }
        ]

        return {
            "sku": sku,
            "size_label": size_label,
            "generation_method": "pattern_first_2d_to_3d_assembly",
            "avatar_skin_cropped": False,
            "scene": scene,
            "components": components,
            "panel_metadata": panel_2d_specs,
            "seam_map": seam_map,
            "surface_attachments": surface_attachments,
            "fabric_profile": fabric_profile,
            "out_glb": out_glb,
        }

    @classmethod
    def _build_authoritative_2d_panels(
        cls,
        *,
        size_label: str,
        half_chest_cm: float,
        back_length_cm: float,
        shoulder_breadth_cm: float,
        sleeve_length_cm: float,
        sleeve_opening_cm: float,
        collar_circ_cm: float,
        hem_width_cm: float,
        pkt_w_cm: float,
        pkt_h_cm: float,
        pkt_x_min: float,
        pkt_y_min: float,
        x_neck_cm: float,
        front_neck_dip_cm: float,
        back_neck_dip_cm: float,
        y_underarm: float,
        y_drop_sh: float,
        front_edges_3d: Dict[str, np.ndarray],
        back_edges_3d: Dict[str, np.ndarray],
        sleeve_l_edges_3d: Dict[str, np.ndarray],
        collar_edges_3d: Dict[str, np.ndarray],
        hem_edges_3d: Dict[str, np.ndarray],
        pocket_edges_3d: Dict[str, np.ndarray],
        components: Dict[str, trimesh.Trimesh],
        y_hem_seam: float,
        collar_h_cm: float = 2.80,
    ) -> List[Dict[str, Any]]:
        """
        Synthesizes explicit, closed 2D flat pattern outlines (cm) with outer seam-allowance cut lines,
        edge lengths computed directly from 2D coordinates, notches, seam allowances, and grainlines.
        """
        side_len_cm = _polyline_length_cm(front_edges_3d["FRONT_SIDE_L"])
        body_h_cm = round(back_length_cm - 2.8, 2)
        half_sh_cm = shoulder_breadth_cm / 2.0
        half_hc_cm = half_chest_cm / 2.0
        half_hem_cm = hem_width_cm / 2.0
        v_underarm_cm = round((y_underarm - y_hem_seam) * 100.0, 2)
        sh_drop_y_cm = round((y_drop_sh - y_hem_seam) * 100.0, 2)

        t_arm_f_len = _polyline_length_cm(front_edges_3d["FRONT_ARMHOLE_L"])
        t_arm_b_len = _polyline_length_cm(back_edges_3d["BACK_ARMHOLE_L"])
        t_neck_f_len = _polyline_length_cm(front_edges_3d["FRONT_NECKLINE"])
        t_neck_b_len = _polyline_length_cm(back_edges_3d["BACK_NECKLINE"])
        t_slv_under_len = _polyline_length_cm(sleeve_l_edges_3d["SLEEVE_UNDERARM_F"])

        def attach_cut_line(panel_dict: Dict[str, Any]) -> Dict[str, Any]:
            outline_cm = panel_dict["outline_2d_cm"]
            sa_cm = float(panel_dict["seam_allowance_cm"])
            cut_cm = _compute_cut_line_2d(outline_cm, sa_cm)
            panel_dict["size_label"] = size_label
            panel_dict["pattern_export_status"] = "ALGORITHMIC_2D_PATTERN_WITH_EXPLICIT_CUTLINE"
            panel_dict["cut_line_2d_cm"] = cut_cm
            panel_dict["stitch_perimeter_cm"] = round(_polyline_length_2d_cm(np.vstack([outline_cm, outline_cm[:1]])), 2)
            panel_dict["cutting_perimeter_cm"] = round(_polyline_length_2d_cm(np.vstack([cut_cm, cut_cm[:1]])), 2)
            return panel_dict

        def make_torso_2d(panel_id: str, name: str, ptype: str, dip_cm: float, neck_target_cm: float, arm_target_cm: float, is_front: bool):
            pfx = "FRONT" if is_front else "BACK"
            e_bot = np.column_stack([np.linspace(-half_hem_cm, half_hem_cm, 17), np.zeros(17)])
            e_side_l = _scale_curve_2d_to_target_length(
                np.column_stack([
                    np.linspace(half_hem_cm, half_hc_cm, 13) + 0.3 * np.sin(np.pi * np.linspace(0, 1, 13)),
                    np.linspace(0.0, v_underarm_cm, 13),
                ]),
                side_len_cm,
            )
            t_a = np.linspace(0.0, 1.0, 15)
            raw_arm_l = np.column_stack([
                half_hc_cm + (half_sh_cm - half_hc_cm) * t_a - 2.2 * np.sin(np.pi * t_a),
                v_underarm_cm + (sh_drop_y_cm - v_underarm_cm) * t_a,
            ])
            e_arm_l = _scale_curve_2d_to_target_length(raw_arm_l, arm_target_cm)
            e_sh_l = np.column_stack([
                np.linspace(half_sh_cm, x_neck_cm, 9),
                np.linspace(sh_drop_y_cm, body_h_cm, 9),
            ])
            t_n = np.linspace(0.0, 1.0, 17)
            raw_neck = np.column_stack([
                x_neck_cm * np.cos(np.pi * t_n),
                body_h_cm - dip_cm * np.sin(np.pi * t_n),
            ])
            e_neck = _scale_curve_2d_to_target_length(raw_neck, neck_target_cm)
            e_sh_r = np.column_stack([
                np.linspace(-x_neck_cm, -half_sh_cm, 9),
                np.linspace(body_h_cm, sh_drop_y_cm, 9),
            ])
            e_arm_r = np.column_stack([-e_arm_l[::-1, 0], e_arm_l[::-1, 1]])
            e_side_r = np.column_stack([-e_side_l[::-1, 0], e_side_l[::-1, 1]])

            edge_segs = [
                (f"{pfx}_BOTTOM_SEAM", e_bot, "seam"),
                (f"{pfx}_SIDE_L", e_side_l, "seam"),
                (f"{pfx}_ARMHOLE_L", e_arm_l, "seam"),
                (f"{pfx}_SHOULDER_L", e_sh_l, "seam"),
                (f"{pfx}_NECKLINE", e_neck, "seam"),
                (f"{pfx}_SHOULDER_R", e_sh_r, "seam"),
                (f"{pfx}_ARMHOLE_R", e_arm_r, "seam"),
                (f"{pfx}_SIDE_R", e_side_r, "seam"),
            ]

            outline = []
            edges_dict = {}
            idx = 0
            for eid, seg, role in edge_segs:
                seg_pts = seg[:-1]
                start_i = idx
                outline.extend(seg_pts.tolist())
                idx += len(seg_pts)
                edges_dict[eid] = {
                    "role": role,
                    "vertex_indices": list(range(start_i, idx)) + [idx if eid != f"{pfx}_SIDE_R" else 0],
                    "coordinates_cm": [[round(float(p[0]), 3), round(float(p[1]), 3)] for p in seg],
                    "length_cm": round(_polyline_length_2d_cm(seg), 2),
                }

            notches = [
                {"notch_id": f"{pfx.lower()}_center_hem", "edge_id": f"{pfx}_BOTTOM_SEAM", "position_cm": [0.0, 0.0]},
                {"notch_id": f"{pfx.lower()}_center_neck", "edge_id": f"{pfx}_NECKLINE", "position_cm": [0.0, round(float(e_neck[len(e_neck)//2, 1]), 2)]},
                {"notch_id": f"{pfx.lower()}_underarm_l", "edge_id": f"{pfx}_SIDE_L", "position_cm": [round(half_hc_cm, 2), v_underarm_cm]},
                {"notch_id": f"{pfx.lower()}_underarm_r", "edge_id": f"{pfx}_SIDE_R", "position_cm": [round(-half_hc_cm, 2), v_underarm_cm]},
            ]

            surf_atts = []
            if is_front:
                px0 = round(pkt_x_min * 100.0, 2)
                px1 = round(px0 + pkt_w_cm, 2)
                py0 = round((pkt_y_min - y_hem_seam) * 100.0, 2)
                py1 = round(py0 + pkt_h_cm, 2)
                path_2d = [
                    [px0, py1],
                    [px0, round(py0 + 1.0, 2)],
                    [round(px0 + 1.0, 2), py0],
                    [round(px1 - 1.0, 2), py0],
                    [px1, round(py0 + 1.0, 2)],
                    [px1, py1],
                ]
                surf_atts.append({
                    "attachment_id": "ATTACH-POCKET-CHEST",
                    "source_panel_id": "PANEL-POCKET-CHEST",
                    "path_2d_cm": path_2d,
                    "path_length_2d_cm": round(_polyline_length_2d_cm(np.array(path_2d)), 2),
                })

            return attach_cut_line({
                "panel_id": panel_id,
                "name": name,
                "pattern_type": ptype,
                "units": "cm",
                "seam_allowance_cm": 1.0,
                "grainline": {"direction": "vertical_warp", "start_cm": [0.0, 8.0], "end_cm": [0.0, round(body_h_cm - 16.2, 1)]},
                "dimensions_2d_cm": {
                    "half_chest_width_cm": half_chest_cm,
                    "hem_seam_width_cm": hem_width_cm,
                    "body_length_hps_to_hem_seam_cm": body_h_cm,
                    "shoulder_breadth_cm": shoulder_breadth_cm,
                    "neckline_dip_cm": round(dip_cm, 2),
                },
                "outline_2d_cm": [[round(p[0], 3), round(p[1], 3)] for p in outline],
                "edges": edges_dict,
                "notches": notches,
                "surface_attachments": surf_atts,
                "mesh_stats": {"vertices": len(components[panel_id].vertices), "faces": len(components[panel_id].faces)},
            })

        def make_sleeve_2d(panel_id: str, name: str):
            cuff_w_cm = 2.0 * sleeve_opening_cm
            half_cuff = cuff_w_cm / 2.0
            v_under = round(t_slv_under_len * 0.96, 2)
            dx_under = math.sqrt(max(t_slv_under_len**2 - v_under**2, 0.0))
            u_top = half_cuff + dx_under

            e_cuff = np.column_stack([np.linspace(-half_cuff, half_cuff, 17), np.zeros(17)])
            e_under_b = np.column_stack([np.linspace(half_cuff, u_top, 9), np.linspace(0.0, v_under, 9)])
            t_cb = np.linspace(0.0, 1.0, 15)
            raw_cap_b = np.column_stack([
                u_top * (1.0 - t_cb),
                v_under + (sleeve_length_cm - v_under) * np.sin(0.5 * np.pi * t_cb),
            ])
            e_cap_b = _scale_curve_2d_to_target_length(raw_cap_b, t_arm_b_len)
            e_cap_f = np.column_stack([-e_cap_b[::-1, 0], e_cap_b[::-1, 1]])
            e_under_f = np.column_stack([np.linspace(-u_top, -half_cuff, 9), np.linspace(v_under, 0.0, 9)])

            edge_segs = [
                ("SLEEVE_CUFF_OPENING", e_cuff, "open_boundary"),
                ("SLEEVE_UNDERARM_B", e_under_b, "seam"),
                ("SLEEVE_CAP_BACK", e_cap_b, "seam"),
                ("SLEEVE_CAP_FRONT", e_cap_f, "seam"),
                ("SLEEVE_UNDERARM_F", e_under_f, "seam"),
            ]
            outline = []
            edges_dict = {}
            idx = 0
            for eid, seg, role in edge_segs:
                seg_pts = seg[:-1]
                start_i = idx
                outline.extend(seg_pts.tolist())
                idx += len(seg_pts)
                edges_dict[eid] = {
                    "role": role,
                    "vertex_indices": list(range(start_i, idx)) + [idx if eid != "SLEEVE_UNDERARM_F" else 0],
                    "coordinates_cm": [[round(float(p[0]), 3), round(float(p[1]), 3)] for p in seg],
                    "length_cm": round(_polyline_length_2d_cm(seg), 2),
                }

            return attach_cut_line({
                "panel_id": panel_id,
                "name": name,
                "pattern_type": "sleeve_bell",
                "units": "cm",
                "seam_allowance_cm": 1.0,
                "grainline": {"direction": "vertical_warp", "start_cm": [0.0, 2.0], "end_cm": [0.0, round(sleeve_length_cm - 3.0, 1)]},
                "dimensions_2d_cm": {
                    "sleeve_length_cm": sleeve_length_cm,
                    "underarm_seam_length_cm": round(_polyline_length_2d_cm(e_under_f), 2),
                    "cuff_opening_flat_width_cm": sleeve_opening_cm,
                    "cuff_opening_circumference_cm": round(cuff_w_cm, 2),
                    "sleeve_cap_front_arc_cm": round(_polyline_length_2d_cm(e_cap_f), 2),
                    "sleeve_cap_back_arc_cm": round(_polyline_length_2d_cm(e_cap_b), 2),
                },
                "outline_2d_cm": [[round(p[0], 3), round(p[1], 3)] for p in outline],
                "edges": edges_dict,
                "notches": [
                    {"notch_id": "shoulder_apex", "edge_id": "SLEEVE_CAP_FRONT", "position_cm": [0.0, round(sleeve_length_cm, 2)]},
                    {"notch_id": "cuff_center", "edge_id": "SLEEVE_CUFF_OPENING", "position_cm": [0.0, 0.0]},
                ],
                "mesh_stats": {"vertices": len(components[panel_id].vertices), "faces": len(components[panel_id].faces)},
            })

        def make_collar_2d():
            h_cm = collar_h_cm
            len_f = t_neck_f_len
            len_b = t_neck_b_len
            tot_seam = len_f + len_b
            half_s = tot_seam / 2.0
            half_top = collar_circ_cm / 2.0
            e_neck_f = np.column_stack([np.linspace(-half_s, -half_s + len_f, 15), np.zeros(15)])
            e_neck_b = np.column_stack([np.linspace(-half_s + len_f, half_s, 15), np.zeros(15)])
            e_join_e = np.column_stack([np.linspace(half_s, half_top, 5), np.linspace(0.0, h_cm, 5)])
            e_top = np.column_stack([np.linspace(half_top, -half_top, 25), np.full(25, h_cm)])
            e_join_s = np.column_stack([np.linspace(-half_top, -half_s, 5), np.linspace(h_cm, 0.0, 5)])

            edge_segs = [
                ("COLLAR_NECK_SEAM_FRONT", e_neck_f, "seam"),
                ("COLLAR_NECK_SEAM_BACK", e_neck_b, "seam"),
                ("COLLAR_JOIN_END", e_join_e, "seam"),
                ("COLLAR_TOP_OPENING", e_top, "open_boundary"),
                ("COLLAR_JOIN_START", e_join_s, "seam"),
            ]
            outline, edges_dict, idx = [], {}, 0
            for eid, seg, role in edge_segs:
                seg_pts = seg[:-1]
                start_i = idx
                outline.extend(seg_pts.tolist())
                idx += len(seg_pts)
                edges_dict[eid] = {
                    "role": role,
                    "vertex_indices": list(range(start_i, idx)) + [idx if eid != "COLLAR_JOIN_START" else 0],
                    "coordinates_cm": [[round(float(p[0]), 3), round(float(p[1]), 3)] for p in seg],
                    "length_cm": round(_polyline_length_2d_cm(seg), 2),
                }
            return attach_cut_line({
                "panel_id": "PANEL-COLLAR-RIB",
                "name": "Ribbed Crewneck Collar (1x1 Rib)",
                "pattern_type": "collar_band",
                "units": "cm",
                "seam_allowance_cm": 0.7,
                "grainline": {"direction": "horizontal_rib_course", "start_cm": [-15.0, 1.4], "end_cm": [15.0, 1.4]},
                "dimensions_2d_cm": {
                    "band_height_cm": h_cm,
                    "collar_seam_circumference_cm": round(tot_seam, 2),
                    "finished_collar_opening_circumference_cm": collar_circ_cm,
                },
                "outline_2d_cm": [[round(p[0], 3), round(p[1], 3)] for p in outline],
                "edges": edges_dict,
                "notches": [
                    {"notch_id": "hps_l_collar", "edge_id": "COLLAR_NECK_SEAM_FRONT", "position_cm": [round(-half_s + len_f, 2), 0.0]},
                ],
                "mesh_stats": {"vertices": len(components["PANEL-COLLAR-RIB"].vertices), "faces": len(components["PANEL-COLLAR-RIB"].faces)},
            })

        def make_hem_2d():
            h_cm = 2.80
            tot_w = 2.0 * hem_width_cm
            half_w = tot_w / 2.0
            e_bot = np.column_stack([np.linspace(-half_w, half_w, 33), np.zeros(33)])
            e_join_e = np.column_stack([np.full(4, half_w), np.linspace(0.0, h_cm, 4)])
            e_top_b = np.column_stack([np.linspace(half_w, 0.0, 17), np.full(17, h_cm)])
            e_top_f = np.column_stack([np.linspace(0.0, -half_w, 17), np.full(17, h_cm)])
            e_join_s = np.column_stack([np.full(4, -half_w), np.linspace(h_cm, 0.0, 4)])

            edge_segs = [
                ("HEM_LOWER_OPENING", e_bot, "open_boundary"),
                ("HEM_JOIN_END", e_join_e, "seam"),
                ("HEM_BODY_SEAM_BACK", e_top_b, "seam"),
                ("HEM_BODY_SEAM_FRONT", e_top_f, "seam"),
                ("HEM_JOIN_START", e_join_s, "seam"),
            ]
            outline, edges_dict, idx = [], {}, 0
            for eid, seg, role in edge_segs:
                seg_pts = seg[:-1]
                start_i = idx
                outline.extend(seg_pts.tolist())
                idx += len(seg_pts)
                edges_dict[eid] = {
                    "role": role,
                    "vertex_indices": list(range(start_i, idx)) + [idx if eid != "HEM_JOIN_START" else 0],
                    "coordinates_cm": [[round(float(p[0]), 3), round(float(p[1]), 3)] for p in seg],
                    "length_cm": round(_polyline_length_2d_cm(seg), 2),
                }
            return attach_cut_line({
                "panel_id": "PANEL-HEM-BAND",
                "name": "Clean 28mm Hem Band",
                "pattern_type": "hem_band",
                "units": "cm",
                "seam_allowance_cm": 0.7,
                "grainline": {"direction": "horizontal_weft", "start_cm": [round(-half_w * 0.75, 1), 1.4], "end_cm": [round(half_w * 0.75, 1), 1.4]},
                "dimensions_2d_cm": {
                    "band_height_cm": h_cm,
                    "hem_flat_width_cm": hem_width_cm,
                    "hem_circumference_cm": tot_w,
                },
                "outline_2d_cm": [[round(p[0], 3), round(p[1], 3)] for p in outline],
                "edges": edges_dict,
                "notches": [
                    {"notch_id": "side_l_hem_band", "edge_id": "HEM_BODY_SEAM_FRONT", "position_cm": [0.0, h_cm]},
                ],
                "mesh_stats": {"vertices": len(components["PANEL-HEM-BAND"].vertices), "faces": len(components["PANEL-HEM-BAND"].faces)},
            })

        def make_pocket_2d():
            hw = pkt_w_cm / 2.0
            bev = 1.0
            e_bot = np.array([[-hw, bev], [-hw + bev, 0.0], [hw - bev, 0.0], [hw, bev]])
            e_side_l = np.array([[hw, bev], [hw, pkt_h_cm]])
            e_top = np.array([[hw, pkt_h_cm], [-hw, pkt_h_cm]])
            e_side_r = np.array([[-hw, pkt_h_cm], [-hw, bev]])
            edge_segs = [
                ("POCKET_BOTTOM", e_bot, "applique_stitch"),
                ("POCKET_SIDE_L", e_side_l, "applique_stitch"),
                ("POCKET_TOP_HEM", e_top, "open_boundary"),
                ("POCKET_SIDE_R", e_side_r, "applique_stitch"),
            ]
            outline, edges_dict, idx = [], {}, 0
            for eid, seg, role in edge_segs:
                seg_pts = seg[:-1]
                start_i = idx
                outline.extend(seg_pts.tolist())
                idx += len(seg_pts)
                edges_dict[eid] = {
                    "role": role,
                    "vertex_indices": list(range(start_i, idx)) + [idx if eid != "POCKET_SIDE_R" else 0],
                    "coordinates_cm": [[round(float(p[0]), 3), round(float(p[1]), 3)] for p in seg],
                    "length_cm": round(_polyline_length_2d_cm(seg), 2),
                }
            return attach_cut_line({
                "panel_id": "PANEL-POCKET-CHEST",
                "name": "Left Chest Patch Pocket",
                "pattern_type": "patch_pocket",
                "units": "cm",
                "seam_allowance_cm": 1.0,
                "grainline": {"direction": "vertical_warp", "start_cm": [0.0, 2.0], "end_cm": [0.0, pkt_h_cm - 2.0]},
                "dimensions_2d_cm": {
                    "width_cm": pkt_w_cm,
                    "height_cm": pkt_h_cm,
                    "corner_style": "beveled_bottom",
                    "placement": "wearer_left_chest",
                },
                "outline_2d_cm": [[round(p[0], 3), round(p[1], 3)] for p in outline],
                "edges": edges_dict,
                "notches": [
                    {"notch_id": "pocket_top_left", "edge_id": "POCKET_TOP_HEM", "position_cm": [round(-hw, 2), pkt_h_cm]},
                    {"notch_id": "pocket_top_right", "edge_id": "POCKET_TOP_HEM", "position_cm": [round(hw, 2), pkt_h_cm]},
                ],
                "mesh_stats": {"vertices": len(components["PANEL-POCKET-CHEST"].vertices), "faces": len(components["PANEL-POCKET-CHEST"].faces)},
            })

        return [
            make_torso_2d("PANEL-FRONT-TORSO", "Front Torso Panel", "front_body", front_neck_dip_cm, t_neck_f_len, t_arm_f_len, is_front=True),
            make_torso_2d("PANEL-BACK-TORSO", "Back Torso Panel", "back_body", back_neck_dip_cm, t_neck_b_len, t_arm_b_len, is_front=False),
            make_sleeve_2d("PANEL-SLEEVE-L", "Left Dropped Sleeve"),
            make_sleeve_2d("PANEL-SLEEVE-R", "Right Dropped Sleeve"),
            make_collar_2d(),
            make_hem_2d(),
            make_pocket_2d(),
        ]

    @classmethod
    def _load_or_create_atlas(cls, texture_atlas_path: Optional[str] = None) -> Image.Image:
        candidates = []
        if texture_atlas_path:
            candidates.append(texture_atlas_path)
        candidates.extend([
            os.path.join(os.getcwd(), "frontend", "public", "garments", "garment_texture_diffuse.png"),
            os.path.join(os.getcwd(), "..", "frontend", "public", "garments", "garment_texture_diffuse.png"),
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "frontend", "public", "garments", "garment_texture_diffuse.png"),
        ])
        for c in candidates:
            if c and os.path.exists(c):
                return Image.open(c).convert("RGBA")
        raise FileNotFoundError("Required PBR texture atlas 'garment_texture_diffuse.png' not found.")
