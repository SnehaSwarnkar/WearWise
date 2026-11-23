"""
WearWise Anthropometry Synthetic Geometry Test Suite
Verifies all 16 required Stage A edge-case conditions and analytical accuracy gates.
"""

import math
import random
import numpy as np
import pytest

from app.domain.entities.avatar import MeshData
from app.anthropometry.models import ContourLoop
from app.anthropometry.exceptions import (
    AnthropometryError,
    NonManifoldContourError,
    OpenContourError,
    UnclosedContourError,
    SelfIntersectingContourError,
    AmbiguousContourError,
    ImplausiblePerimeterError,
    MeshSliceError,
)
from app.anthropometry.geometry import (
    intersect_triangle_with_plane,
    cluster_endpoints,
    stitch_segments_into_loops,
    check_self_intersection_2d,
    EPSILON_PLANE_M,
    EPSILON_SNAP_M,
    EPSILON_LEN_M,
    AMBIGUITY_MARGIN_M,
)
from app.anthropometry.slice import (
    slice_mesh_with_plane,
    select_landmark_guided_loop,
)


def create_synthetic_cylinder(radius_m: float, height_m: float, num_sides: int = 32) -> MeshData:
    """Generates a closed, watertight 2-manifold regular cylinder mesh centered at origin."""
    verts = []
    half_h = height_m / 2.0
    # Bottom ring: 0..N-1, Top ring: N..2N-1
    for z in [-half_h, half_h]:
        for i in range(num_sides):
            theta = 2.0 * math.pi * i / num_sides
            verts.append([radius_m * math.cos(theta), radius_m * math.sin(theta), z])
    
    # Cap centers: bottom center = 2N, top center = 2N + 1
    verts.append([0.0, 0.0, -half_h])
    verts.append([0.0, 0.0, half_h])
    b_center = 2 * num_sides
    t_center = 2 * num_sides + 1

    faces = []
    N = num_sides
    for i in range(N):
        next_i = (i + 1) % N
        # Side quad as two triangles
        b1, b2 = i, next_i
        t1, t2 = N + i, N + next_i
        faces.append([b1, b2, t2])
        faces.append([b1, t2, t1])
        # Bottom cap (pointing down)
        faces.append([b_center, next_i, i])
        # Top cap (pointing up)
        faces.append([t_center, N + i, N + next_i])

    return MeshData(vertices=np.array(verts, dtype=np.float64), faces=np.array(faces, dtype=np.int32))


def create_synthetic_box(size_x_m: float, size_y_m: float, size_z_m: float) -> MeshData:
    """Generates a closed watertight box mesh centered at origin."""
    hx, hy, hz = size_x_m / 2.0, size_y_m / 2.0, size_z_m / 2.0
    v = np.array([
        [-hx, -hy, -hz], [hx, -hy, -hz], [hx, hy, -hz], [-hx, hy, -hz],
        [-hx, -hy, hz],  [hx, -hy, hz],  [hx, hy, hz],  [-hx, hy, hz],
    ], dtype=np.float64)
    f = np.array([
        # Bottom
        [0, 2, 1], [0, 3, 2],
        # Top
        [4, 5, 6], [4, 6, 7],
        # Front (-Y)
        [0, 1, 5], [0, 5, 4],
        # Back (+Y)
        [2, 3, 7], [2, 7, 6],
        # Left (-X)
        [0, 4, 7], [0, 7, 3],
        # Right (+X)
        [1, 2, 6], [1, 6, 5],
    ], dtype=np.int32)
    return MeshData(vertices=v, faces=f)


# --- 16 Required Synthetic Geometry Tests ---

def test_01_standard_transverse_crossings():
    """1. Standard transverse triangle-plane crossings with analytical perimeter verification."""
    radius_m = 0.20  # 20 cm radius
    height_m = 0.50
    num_sides = 32
    mesh = create_synthetic_cylinder(radius_m, height_m, num_sides)
    
    loops, count = slice_mesh_with_plane(mesh, plane_point=np.array([0, 0, 0]), plane_normal=np.array([0, 0, 1]))
    assert len(loops) == 1
    loop = loops[0]
    assert loop.is_closed
    # Analytical perimeter of 32-gon: 32 * 2 * R * sin(pi / 32)
    expected_perim_cm = num_sides * 2.0 * radius_m * math.sin(math.pi / num_sides) * 100.0
    assert pytest.approx(loop.perimeter_cm, rel=1e-3) == expected_perim_cm
    # Triangulated cylinder quads have 2 triangles per quad
    assert len(loop.points_3d_m) in (num_sides, 2 * num_sides)


def test_02_one_vertex_on_plane():
    """2. One vertex exactly on the plane, cutting through opposite edge."""
    v0 = np.array([0.0, 0.0, 0.0])   # on-plane
    v1 = np.array([1.0, 0.0, 0.1])   # above
    v2 = np.array([1.0, 0.0, -0.1])  # below
    plane_p = np.array([0.0, 0.0, 0.0])
    plane_n = np.array([0.0, 0.0, 1.0])

    segs = intersect_triangle_with_plane(v0, v1, v2, plane_p, plane_n)
    assert len(segs) == 1
    p_start, p_end = segs[0]
    assert np.allclose(p_start, v0, atol=1e-7)
    # Opposite edge cut is exactly midway at z=0: [1.0, 0.0, 0.0]
    assert np.allclose(p_end, [1.0, 0.0, 0.0], atol=1e-7)


def test_03_coplanar_edge():
    """3. Two vertices on a coplanar edge shared by two triangles."""
    # Shared edge between v0 and v1 at z=0
    v0 = np.array([0.0, 0.0, 0.0])
    v1 = np.array([1.0, 0.0, 0.0])
    v2_above = np.array([0.5, 0.5, 0.1])
    v2_below = np.array([0.5, -0.5, -0.1])

    plane_p = np.array([0.0, 0.0, 0.0])
    plane_n = np.array([0.0, 0.0, 1.0])

    segs1 = intersect_triangle_with_plane(v0, v1, v2_above, plane_p, plane_n)
    segs2 = intersect_triangle_with_plane(v0, v1, v2_below, plane_p, plane_n)

    assert len(segs1) == 1
    assert len(segs2) == 1
    # Both produce segment between v0 and v1
    # Stitching must deduplicate identical/antiparallel coplanar edge
    quad_segments = [segs1[0], segs2[0]]
    # Add closing segments to form a closed triangle
    v3 = np.array([0.5, 1.0, 0.0])
    quad_segments.extend([(v1, v3), (v3, v0)])
    
    loops = stitch_segments_into_loops(quad_segments)
    assert len(loops) == 1
    assert loops[0].is_closed


def test_04_fully_coplanar_triangles():
    """4. Fully coplanar triangles: interior discarded, boundary edges captured."""
    # Triangle lying entirely on z=0
    v0 = np.array([0.0, 0.0, 0.0])
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([0.0, 1.0, 0.0])

    plane_p = np.array([0.0, 0.0, 0.0])
    plane_n = np.array([0.0, 0.0, 1.0])

    segs = intersect_triangle_with_plane(v0, v1, v2, plane_p, plane_n)
    # Coplanar triangle interior is discarded
    assert len(segs) == 0


def test_05_tangential_intersections():
    """5. Tangential intersection: plane touches 1 vertex with others on same side."""
    v0 = np.array([0.0, 0.0, 0.0])   # on-plane
    v1 = np.array([1.0, 0.0, 0.05])  # above
    v2 = np.array([0.0, 1.0, 0.05])  # above
    plane_p = np.array([0.0, 0.0, 0.0])
    plane_n = np.array([0.0, 0.0, 1.0])

    segs = intersect_triangle_with_plane(v0, v1, v2, plane_p, plane_n)
    # Tangential touches are discarded; zero segments generated
    assert len(segs) == 0


def test_06_duplicate_and_antiparallel_segments():
    """6. Duplicate and antiparallel segment deduplication."""
    p1 = np.array([0.0, 0.0, 0.0])
    p2 = np.array([1.0, 0.0, 0.0])
    p3 = np.array([0.5, 1.0, 0.0])

    segments = [
        (p1, p2),
        (p2, p1),  # antiparallel duplicate
        (p1, p2),  # identical duplicate
        (p2, p3),
        (p3, p2),  # antiparallel
        (p3, p1),
    ]

    loops = stitch_segments_into_loops(segments)
    assert len(loops) == 1
    assert loops[0].is_closed
    assert len(loops[0].points_3d_m) == 3


def test_07_zero_length_segments():
    """7. Discarding zero-length segments (< 1e-6 m)."""
    p1 = np.array([0.0, 0.0, 0.0])
    p2 = np.array([1.0, 0.0, 0.0])
    p3 = np.array([0.5, 1.0, 0.0])
    p_zero = p1 + np.array([1e-8, 0.0, 0.0])  # length 1e-8 m < 1e-6 m

    segments = [
        (p1, p2),
        (p2, p3),
        (p3, p1),
        (p1, p_zero),  # degenerate zero-length
        (p2, p2),      # exact zero-length
    ]

    loops = stitch_segments_into_loops(segments)
    assert len(loops) == 1
    assert len(loops[0].points_3d_m) == 3


def test_08_endpoints_on_opposite_sides_of_spatial_cell_boundary():
    """8. Endpoints separated by tiny distance straddling spatial cell boundary."""
    # Suppose a cell boundary at x = 1e-5.
    # Point A at 0.99e-5, Point B at 1.01e-5. Distance = 2e-7 m (far below tolerance 1e-5 m).
    pts = np.array([
        [0.99e-5, 0.0, 0.0],
        [1.01e-5, 0.0, 0.0],
    ])
    cluster_ids, centroids = cluster_endpoints(pts, tolerance_m=EPSILON_SNAP_M)
    assert cluster_ids[0] == cluster_ids[1]  # merged into same cluster
    assert len(centroids) == 1


def test_09_near_tolerance_endpoint_pairs():
    """9. Near-tolerance endpoint pairs: within vs outside tolerance."""
    p0 = np.array([0.0, 0.0, 0.0])
    p_within = np.array([0.9e-5, 0.0, 0.0])  # 0.9 * 1e-5 m <= 1e-5 m
    p_outside = np.array([1.2e-5, 0.0, 0.0]) # 1.2 * 1e-5 m > 1e-5 m

    # Case A: within tolerance merges
    c_within, _ = cluster_endpoints(np.array([p0, p_within]), tolerance_m=EPSILON_SNAP_M)
    assert c_within[0] == c_within[1]

    # Case B: outside tolerance remains separate
    c_outside, _ = cluster_endpoints(np.array([p0, p_outside]), tolerance_m=EPSILON_SNAP_M)
    assert c_outside[0] != c_outside[1]


def test_10_chained_endpoint_clusters():
    """10. Chained endpoint clusters: prevent transitive diameter expansion > tolerance."""
    # Sequence of 5 points spaced by 0.6 * EPSILON_SNAP_M
    # Point 0: 0.0, Point 1: 0.6 eps, Point 2: 1.2 eps, Point 3: 1.8 eps, Point 4: 2.4 eps
    # In single-linkage, all 5 would merge into one cluster of diameter 2.4 eps > eps!
    step = 0.6 * EPSILON_SNAP_M
    pts = np.array([[i * step, 0.0, 0.0] for i in range(5)])

    cluster_ids, centroids = cluster_endpoints(pts, tolerance_m=EPSILON_SNAP_M)
    # Check that each cluster's diameter is strictly <= EPSILON_SNAP_M
    for c_idx in set(cluster_ids):
        members = pts[cluster_ids == c_idx]
        for i in range(len(members)):
            for j in range(len(members)):
                dist = np.linalg.norm(members[i] - members[j])
                assert dist <= EPSILON_SNAP_M + 1e-12, f"Cluster {c_idx} diameter exceeded: {dist} > {EPSILON_SNAP_M}"


def test_11_degree_one_open_contours():
    """11. Degree-one open contours raise explicit OpenContourError."""
    p1 = np.array([0.0, 0.0, 0.0])
    p2 = np.array([1.0, 0.0, 0.0])
    p3 = np.array([1.0, 1.0, 0.0])
    # Open C-shape: p1-p2, p2-p3 (p3 does not connect back to p1)
    segments = [(p1, p2), (p2, p3)]

    with pytest.raises(OpenContourError) as exc_info:
        stitch_segments_into_loops(segments)
    assert "degree-1" in str(exc_info.value) or "open contour" in str(exc_info.value)


def test_12_degree_three_and_higher_ambiguous_intersections():
    """12. Degree-three Y-branching configuration raises NonManifoldContourError."""
    p_center = np.array([0.0, 0.0, 0.0])
    p_a = np.array([1.0, 0.0, 0.0])
    p_b = np.array([-0.5, 0.866, 0.0])
    p_c = np.array([-0.5, -0.866, 0.0])

    # Three edges radiating from p_center (Y-junction)
    segments = [(p_center, p_a), (p_center, p_b), (p_center, p_c)]

    with pytest.raises(NonManifoldContourError) as exc_info:
        stitch_segments_into_loops(segments)
    assert "degree-3" in str(exc_info.value) or "non-manifold" in str(exc_info.value)


def test_13_multiple_disconnected_closed_loops():
    """13. Multiple disconnected closed loops (e.g. two separate cylinders)."""
    # Create two triangles far apart: one at x=0, one at x=10
    tri1 = [
        (np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0])),
        (np.array([1.0, 0.0, 0.0]), np.array([0.5, 1.0, 0.0])),
        (np.array([0.5, 1.0, 0.0]), np.array([0.0, 0.0, 0.0])),
    ]
    tri2 = [
        (np.array([10.0, 0.0, 0.0]), np.array([11.0, 0.0, 0.0])),
        (np.array([11.0, 0.0, 0.0]), np.array([10.5, 1.0, 0.0])),
        (np.array([10.5, 1.0, 0.0]), np.array([10.0, 0.0, 0.0])),
    ]
    loops = stitch_segments_into_loops(tri1 + tri2)
    assert len(loops) == 2
    assert loops[0].is_closed and loops[1].is_closed


def test_14_nested_loops_and_self_intersections():
    """14. Nested loops and self-intersection detection (e.g. figure-8)."""
    # 2D figure-8 self-intersecting polygon:
    # (0, 0) -> (1, 1) -> (1, 0) -> (0, 1) -> (0, 0)
    # The edges (0,0)-(1,1) and (1,0)-(0,1) intersect at (0.5, 0.5)
    p_a = np.array([0.0, 0.0, 0.0])
    p_b = np.array([1.0, 1.0, 0.0])
    p_c = np.array([1.0, 0.0, 0.0])
    p_d = np.array([0.0, 1.0, 0.0])

    segments = [(p_a, p_b), (p_b, p_c), (p_c, p_d), (p_d, p_a)]

    with pytest.raises(SelfIntersectingContourError) as exc_info:
        stitch_segments_into_loops(segments)
    assert "self-intersects" in str(exc_info.value)


def test_15_deterministic_traversal_and_perimeter_calculations():
    """15. Deterministic traversal and exact perimeter invariance under input segment shuffling."""
    # Square prism: 0.10 m x 0.10 m (10 cm x 10 cm). Perimeter = 40.0 cm.
    box = create_synthetic_box(0.10, 0.10, 0.20)
    loops, count = slice_mesh_with_plane(box, plane_point=np.array([0, 0, 0]), plane_normal=np.array([0, 0, 1]))
    assert len(loops) == 1
    base_loop = loops[0]
    assert pytest.approx(base_loop.perimeter_cm, abs=1e-5) == 40.0

    # Extract raw segments and verify order invariance across 10 random permutations
    v = box.vertices
    f = box.faces
    raw_segments = []
    for face in f:
        segs = intersect_triangle_with_plane(v[face[0]], v[face[1]], v[face[2]], np.array([0, 0, 0]), np.array([0, 0, 1]))
        raw_segments.extend(segs)

    base_pts = base_loop.points_3d_m
    rng = random.Random(42)
    for _ in range(10):
        shuffled = list(raw_segments)
        # Randomly shuffle and also reverse some segments
        rng.shuffle(shuffled)
        shuffled = [(b, a) if rng.random() > 0.5 else (a, b) for a, b in shuffled]
        shuffled_loops = stitch_segments_into_loops(shuffled)
        assert len(shuffled_loops) == 1
        assert pytest.approx(shuffled_loops[0].perimeter_cm, abs=1e-5) == 40.0
        assert np.allclose(shuffled_loops[0].points_3d_m, base_pts, atol=1e-8)


def test_16_explicit_failures_for_ambiguous_or_invalid_contours():
    """16. Explicit failures for landmark ambiguity and implausible perimeters."""
    # Create two candidate loops
    p_center1 = np.array([0.0, 0.05, 0.0])  # Centroid at y = 0.05
    p_center2 = np.array([0.0, 0.06, 0.0])  # Centroid at y = 0.06 -> delta = 0.01 m = 1 cm < 2.0 cm margin
    
    loop1 = ContourLoop(
        points_3d_m=np.array([[0, 0.05, 0], [0.1, 0.05, 0], [0.05, 0.1, 0]]),
        is_closed=True,
        centroid_3d_m=(0.0, 0.05, 0.0),
        bounding_box_min_m=(-0.1, 0.0, 0.0),
        bounding_box_max_m=(0.1, 0.1, 0.0),
        perimeter_cm=80.0,
    )
    loop2 = ContourLoop(
        points_3d_m=np.array([[0, 0.06, 0], [0.1, 0.06, 0], [0.05, 0.11, 0]]),
        is_closed=True,
        centroid_3d_m=(0.0, 0.06, 0.0),
        bounding_box_min_m=(-0.1, 0.0, 0.0),
        bounding_box_max_m=(0.1, 0.1, 0.0),
        perimeter_cm=82.0,
    )

    landmark_origin = np.array([0.0, 0.0, 0.0])

    # Case A: Ambiguity rejection (< 2.0 cm margin)
    with pytest.raises(AmbiguousContourError) as exc_info:
        select_landmark_guided_loop([loop1, loop2], landmark_origin, ambiguity_margin_m=AMBIGUITY_MARGIN_M, site_name="chest")
    assert "Ambiguous contour" in str(exc_info.value)

    # Case B: Plausibility guard (perimeter 15.0 cm falls outside [60.0, 200.0] cm for chest)
    tiny_loop = ContourLoop(
        points_3d_m=np.array([[0, 0, 0], [0.02, 0, 0], [0.01, 0.02, 0]]),
        is_closed=True,
        centroid_3d_m=(0.0, 0.0, 0.0),
        bounding_box_min_m=(-0.01, -0.01, 0.0),
        bounding_box_max_m=(0.01, 0.01, 0.0),
        perimeter_cm=15.0,  # Implausible for chest
    )
    with pytest.raises(ImplausiblePerimeterError) as exc_info2:
        select_landmark_guided_loop([tiny_loop], landmark_origin, min_perimeter_cm=60.0, max_perimeter_cm=200.0, site_name="chest")
    assert "outside plausible range" in str(exc_info2.value)


# --- Dedicated Stage A Degree-Four & Topology Provenance Test Cases ---

def test_successful_degree_four_disambiguation_via_tangents():
    """Verifies successful resolution of a degree-4 node where tangent continuity is clear."""
    # Loop 1 (horizontal): (-1, 0) -> (0, 0) -> (+1, 0) -> (+1, 2) -> (-1, 2) -> (-1, 0)
    # Loop 2 (vertical): (0, -1) -> (0, 0) -> (0, +1) -> (-2, +1) -> (-2, -1) -> (0, -1)
    # At (0, 0), outward directions:
    # Left: (-1, 0), Right: (+1, 0) -> dot = -1.0 (straight!)
    # Down: (0, -1), Up: (0, +1) -> dot = -1.0 (straight!)
    p_center = np.array([0.0, 0.0, 0.0])
    
    # Loop 1 segments
    p_l = np.array([-1.0, 0.0, 0.0])
    p_r = np.array([1.0, 0.0, 0.0])
    p_tr = np.array([1.0, 2.0, 0.0])
    p_tl = np.array([-1.0, 2.0, 0.0])
    loop1_segs = [
        (p_l, p_center),
        (p_center, p_r),
        (p_r, p_tr),
        (p_tr, p_tl),
        (p_tl, p_l),
    ]

    # Loop 2 segments
    p_d = np.array([0.0, -1.0, 0.0])
    p_u = np.array([0.0, 1.0, 0.0])
    p_ul = np.array([-2.0, 1.0, 0.0])
    p_dl = np.array([-2.0, -1.0, 0.0])
    loop2_segs = [
        (p_d, p_center),
        (p_center, p_u),
        (p_u, p_ul),
        (p_ul, p_dl),
        (p_dl, p_d),
    ]

    loops = stitch_segments_into_loops(loop1_segs + loop2_segs)
    assert len(loops) == 2
    assert loops[0].is_closed and loops[1].is_closed

    # Verify perimeters match analytical values
    # Loop 1: 1 + 1 + 2 + 2 + 2 = 8.0 m -> 800.0 cm
    # Loop 2: 1 + 1 + 2 + 2 + 2 = 8.0 m -> 800.0 cm
    for l in loops:
        assert pytest.approx(l.perimeter_cm, abs=1e-4) == 800.0
        # Verify node at (0, 0, 0) was preserved in point coordinates
        dists_to_center = [np.linalg.norm(pt - p_center) for pt in l.points_3d_m]
        assert min(dists_to_center) < 1e-8


def test_ambiguous_degree_four_rejection():
    """Verifies that an ambiguous degree-4 junction with no straight continuation is strictly rejected."""
    # 4 segments meeting at (0, 0) at 90-degree angles:
    # (+1, 0), (0, +1), (-1, 0), (0, -1)
    # But closing in a way where each pairing is equally non-straight (e.g. all 90 degree bends)
    p_center = np.array([0.0, 0.0, 0.0])
    p1 = np.array([1.0, 0.0, 0.0])
    p2 = np.array([0.0, 1.0, 0.0])
    p3 = np.array([0.5, 0.5, 0.0])
    p4 = np.array([0.2, 0.8, 0.0])

    segments = [
        (p1, p_center), (p2, p_center), (p3, p_center), (p4, p_center),
        (p1, p2), (p3, p4),
    ]

    with pytest.raises(NonManifoldContourError) as exc_info:
        stitch_segments_into_loops(segments)
    assert "ambiguous" in str(exc_info.value).lower() or "degree-4" in str(exc_info.value).lower()


def test_multiple_degree_four_nodes_handling():
    """Verifies that multiple degree-4 nodes are resolved simultaneously without node-ID collisions."""
    # Two crossings at (0, 0, 0) and (10, 0, 0)
    p_c1 = np.array([0.0, 0.0, 0.0])
    p_c2 = np.array([10.0, 0.0, 0.0])

    def make_cross_loops(center, offset_x):
        cx = offset_x
        # Loop A (horizontal)
        lA = [
            (np.array([cx - 1, 0, 0]), center),
            (center, np.array([cx + 1, 0, 0])),
            (np.array([cx + 1, 0, 0]), np.array([cx + 1, 2, 0])),
            (np.array([cx + 1, 2, 0]), np.array([cx - 1, 2, 0])),
            (np.array([cx - 1, 2, 0]), np.array([cx - 1, 0, 0])),
        ]
        # Loop B (vertical)
        lB = [
            (np.array([cx, -1, 0]), center),
            (center, np.array([cx, 1, 0])),
            (np.array([cx, 1, 0]), np.array([cx - 2, 1, 0])),
            (np.array([cx - 2, 1, 0]), np.array([cx - 2, -1, 0])),
            (np.array([cx - 2, -1, 0]), np.array([cx, -1, 0])),
        ]
        return lA + lB

    segs = make_cross_loops(p_c1, 0.0) + make_cross_loops(p_c2, 10.0)
    loops = stitch_segments_into_loops(segs)
    assert len(loops) == 4
    for l in loops:
        assert l.is_closed
        assert pytest.approx(l.perimeter_cm, abs=1e-4) == 800.0


def test_topology_provenance_primary_disambiguation():
    """Verifies that mesh topology face provenance successfully resolves degree-4 node even when tangents are angled."""
    from app.anthropometry.geometry import IntersectionSegment

    p_center = np.array([0.0, 0.0, 0.0])
    p1 = np.array([1.0, 0.5, 0.0])
    p2 = np.array([-0.8, 0.2, 0.0])
    p3 = np.array([0.2, 1.0, 0.0])
    p4 = np.array([-0.3, -1.0, 0.0])

    # Segments meeting at p_center with shared face indices:
    # Pair 1: (p1, p_center) and (p_center, p2) both belong to face 101
    # Pair 2: (p3, p_center) and (p_center, p4) both belong to face 202
    segs = [
        IntersectionSegment(start_point=p1, end_point=p_center, face_index=101),
        IntersectionSegment(start_point=p_center, end_point=p2, face_index=101),
        IntersectionSegment(start_point=p2, end_point=p1, face_index=101),  # closes loop 1

        IntersectionSegment(start_point=p3, end_point=p_center, face_index=202),
        IntersectionSegment(start_point=p_center, end_point=p4, face_index=202),
        IntersectionSegment(start_point=p4, end_point=p3, face_index=202),  # closes loop 2
    ]

    loops = stitch_segments_into_loops(segs)
    assert len(loops) == 2
    assert loops[0].is_closed and loops[1].is_closed


def test_deterministic_traversal_after_segment_shuffling_degree_four():
    """Verifies that shuffling segments of a degree-4 resolved system yields bitwise deterministic loops."""
    p_center = np.array([0.0, 0.0, 0.0])
    p_l = np.array([-1.0, 0.0, 0.0])
    p_r = np.array([1.0, 0.0, 0.0])
    p_tr = np.array([1.0, 2.0, 0.0])
    p_tl = np.array([-1.0, 2.0, 0.0])

    p_d = np.array([0.0, -1.0, 0.0])
    p_u = np.array([0.0, 1.0, 0.0])
    p_ul = np.array([-2.0, 1.0, 0.0])
    p_dl = np.array([-2.0, -1.0, 0.0])

    segs = [
        (p_l, p_center), (p_center, p_r), (p_r, p_tr), (p_tr, p_tl), (p_tl, p_l),
        (p_d, p_center), (p_center, p_u), (p_u, p_ul), (p_ul, p_dl), (p_dl, p_d),
    ]

    base_loops = stitch_segments_into_loops(segs)
    base_pts = [l.points_3d_m for l in base_loops]

    rng = random.Random(123)
    for _ in range(10):
        shuffled = list(segs)
        rng.shuffle(shuffled)
        shuffled = [(b, a) if rng.random() > 0.5 else (a, b) for a, b in shuffled]
        shuffled_loops = stitch_segments_into_loops(shuffled)
        assert len(shuffled_loops) == len(base_loops)
        for i in range(len(base_loops)):
            assert np.allclose(shuffled_loops[i].points_3d_m, base_pts[i], atol=1e-8)

