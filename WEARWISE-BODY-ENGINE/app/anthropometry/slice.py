"""
WearWise Anthropometry Mesh-Plane Slicing and Landmark Selection
Integrates triangle intersection with landmark proximity, ambiguity rejection, and regional masking.
"""

from typing import List, Tuple, Set, Optional, Dict, Any
import math
import numpy as np

from app.domain.entities.avatar import MeshData
from app.anthropometry.models import ContourLoop, ExtractionDiagnostic
from app.anthropometry.exceptions import (
    MeshSliceError,
    AmbiguousContourError,
    ImplausiblePerimeterError,
)
from app.anthropometry.geometry import (
    intersect_triangle_with_plane,
    stitch_segments_into_loops,
    IntersectionSegment,
    EPSILON_PLANE_M,
    EPSILON_SNAP_M,
    EPSILON_LEN_M,
    AMBIGUITY_MARGIN_M,
)


def slice_mesh_with_plane(
    mesh: MeshData,
    plane_point: np.ndarray,
    plane_normal: np.ndarray,
    region_vertex_mask: Optional[Set[int]] = None,
    tolerance_m: float = EPSILON_SNAP_M,
) -> Tuple[List[ContourLoop], int]:
    """
    Slices a 3D MeshData object with an arbitrary cutting plane.
    
    If region_vertex_mask is provided, filters faces so that a face (v0, v1, v2)
    is sliced only if at least 2 of its 3 vertices are in the mask.
    
    Returns:
    - loops: List of stitched, closed ContourLoops.
    - intersected_triangles_count: Number of faces that generated valid intersection segments.
    """
    verts = mesh.vertices
    faces = mesh.faces

    p0 = np.asarray(plane_point, dtype=np.float64)
    normal = np.asarray(plane_normal, dtype=np.float64)
    norm = np.linalg.norm(normal)
    if norm < 1e-12:
        raise ValueError("Plane normal must be non-zero")
    normal = normal / norm

    # Quick AABB bounding box check against plane
    bb_min = np.min(verts, axis=0)
    bb_max = np.max(verts, axis=0)

    # Compute signed distances for all 8 bounding box corners
    corners = np.array([
        [x, y, z]
        for x in (bb_min[0], bb_max[0])
        for y in (bb_min[1], bb_max[1])
        for z in (bb_min[2], bb_max[2])
    ])
    corner_dists = np.dot(corners - p0, normal)
    if np.all(corner_dists > EPSILON_PLANE_M) or np.all(corner_dists < -EPSILON_PLANE_M):
        # Plane completely misses mesh bounding box
        return [], 0

    all_segments: List[IntersectionSegment] = []
    intersected_count = 0

    for f_idx in range(len(faces)):
        i0, i1, i2 = faces[f_idx]

        # Apply region mask filter if present (require >= 2 vertices in mask)
        if region_vertex_mask is not None:
            mask_count = (
                (1 if i0 in region_vertex_mask else 0) +
                (1 if i1 in region_vertex_mask else 0) +
                (1 if i2 in region_vertex_mask else 0)
            )
            if mask_count < 2:
                continue

        v0, v1, v2 = verts[i0], verts[i1], verts[i2]
        segs = intersect_triangle_with_plane(
            v0, v1, v2,
            plane_point=p0,
            plane_normal=normal,
            epsilon_plane_m=EPSILON_PLANE_M,
            epsilon_len_m=EPSILON_LEN_M,
        )
        if segs:
            intersected_count += 1
            for s_start, s_end in segs:
                all_segments.append(IntersectionSegment(
                    start_point=s_start,
                    end_point=s_end,
                    face_index=f_idx,
                ))

    if not all_segments:
        return [], 0

    loops = stitch_segments_into_loops(all_segments, tolerance_m=tolerance_m)
    return loops, intersected_count


def select_landmark_guided_loop(
    loops: List[ContourLoop],
    landmark_point_m: np.ndarray,
    ambiguity_margin_m: float = AMBIGUITY_MARGIN_M,
    min_perimeter_cm: float = 20.0,
    max_perimeter_cm: float = 250.0,
    site_name: str = "measurement",
) -> Tuple[ContourLoop, int]:
    """
    Selects the candidate loop whose centroid is closest in horizontal planar distance
    to the designated anatomical landmark.
    
    Enforces:
    - Safe failure if no loops exist.
    - Ambiguity margin gate: rejects if two nearest loops are within ambiguity_margin_m.
    - Anatomical plausibility guard: rejects if perimeter is outside [min_perim, max_perim].
    """
    if not loops:
        raise MeshSliceError(f"No contour loops available for site '{site_name}'")

    lm = np.asarray(landmark_point_m, dtype=np.float64)

    # Compute planar horizontal distance D(L_j) = sqrt((Xc - X_lm)^2 + (Yc - Y_lm)^2)
    distances: List[Tuple[float, int, ContourLoop]] = []
    for idx, loop in enumerate(loops):
        cx, cy, _ = loop.centroid_3d_m
        dist_2d = math.sqrt((cx - lm[0]) ** 2 + (cy - lm[1]) ** 2)
        distances.append((dist_2d, idx, loop))

    # Sort ascending by 2D distance
    distances.sort(key=lambda x: x[0])

    # Ambiguity check
    if len(distances) >= 2:
        d1 = distances[0][0]
        d2 = distances[1][0]
        diff = abs(d1 - d2)
        if diff < ambiguity_margin_m:
            raise AmbiguousContourError(
                f"Ambiguous contour selection for site '{site_name}': nearest loops have distance delta {diff*100.0:.2f} cm < {ambiguity_margin_m*100.0:.1f} cm",
                details={
                    "site": site_name,
                    "d1_cm": d1 * 100.0,
                    "d2_cm": d2 * 100.0,
                    "margin_cm": ambiguity_margin_m * 100.0,
                },
            )

    selected_dist, selected_idx, selected_loop = distances[0]

    # Plausibility check
    if not (min_perimeter_cm <= selected_loop.perimeter_cm <= max_perimeter_cm):
        raise ImplausiblePerimeterError(
            f"Extracted perimeter {selected_loop.perimeter_cm:.2f} cm for '{site_name}' is outside plausible range [{min_perimeter_cm:.1f}, {max_perimeter_cm:.1f}] cm",
            details={
                "site": site_name,
                "perimeter_cm": selected_loop.perimeter_cm,
                "range_cm": (min_perimeter_cm, max_perimeter_cm),
            },
        )

    return selected_loop, selected_idx
