"""
WearWise Anthropometry Geometry Engine
Exact triangle-mesh-plane intersection, diameter-bounded endpoint clustering,
deterministic loop stitching, degree-2 graph validation, and perimeter calculation.
"""

from typing import List, Tuple, Dict, Set, Optional, Any
import math
import numpy as np
from scipy.spatial import KDTree

from app.anthropometry.models import ContourLoop
from app.anthropometry.exceptions import (
    NonManifoldContourError,
    OpenContourError,
    UnclosedContourError,
    SelfIntersectingContourError,
    AmbiguousContourError,
)

# Canonical tolerances specified in Rev 1.2.1
EPSILON_PLANE_M: float = 1e-6   # Signed distance plane classification (1 micrometer)
EPSILON_SNAP_M: float = 1e-5    # Endpoint snapping / clustering tolerance (10 micrometers)
EPSILON_LEN_M: float = 1e-6     # Minimum valid segment length (1 micrometer)
AMBIGUITY_MARGIN_M: float = 0.02 # Ambiguity threshold between nearest loops (2.0 cm)


def intersect_triangle_with_plane(
    v0: np.ndarray,
    v1: np.ndarray,
    v2: np.ndarray,
    plane_point: np.ndarray,
    plane_normal: np.ndarray,
    epsilon_plane_m: float = EPSILON_PLANE_M,
    epsilon_len_m: float = EPSILON_LEN_M,
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Computes exact line segment(s) resulting from intersecting a 3D triangle with a cutting plane.
    
    Handles:
    - Standard transverse crossing (1 vertex on one side, 2 on the other)
    - One vertex on-plane, others on opposite sides
    - Coplanar edge (2 vertices on-plane)
    - Coplanar face (all 3 vertices on-plane -> interior discarded)
    - Tangential touch (1 vertex on-plane, others on same side -> discarded)
    """
    verts = [np.asarray(v0, dtype=np.float64), np.asarray(v1, dtype=np.float64), np.asarray(v2, dtype=np.float64)]
    p0 = np.asarray(plane_point, dtype=np.float64)
    normal = np.asarray(plane_normal, dtype=np.float64)
    norm_len = np.linalg.norm(normal)
    if norm_len < 1e-12:
        raise ValueError("Plane normal must be non-zero")
    normal = normal / norm_len

    # Signed distances to plane
    d = [float(np.dot(verts[i] - p0, normal)) for i in range(3)]
    
    # Snap near-zero distances to exact 0.0
    for i in range(3):
        if abs(d[i]) <= epsilon_plane_m:
            d[i] = 0.0

    signs = [0 if d[i] == 0.0 else (1 if d[i] > 0.0 else -1) for i in range(3)]
    num_zeros = signs.count(0)
    num_pos = signs.count(1)
    num_neg = signs.count(-1)

    segments: List[Tuple[np.ndarray, np.ndarray]] = []

    # Case 1: Fully coplanar triangle (all 3 vertices on plane)
    if num_zeros == 3:
        # Discard face interior to prevent interior cross-hatched webs
        return []

    # Case 2: Coplanar edge (2 vertices on plane, 1 off-plane)
    if num_zeros == 2:
        zero_indices = [i for i in range(3) if signs[i] == 0]
        p_a = verts[zero_indices[0]]
        p_b = verts[zero_indices[1]]
        if np.linalg.norm(p_a - p_b) >= epsilon_len_m:
            segments.append((p_a, p_b))
        return segments

    # Case 3: One vertex on plane
    if num_zeros == 1:
        zero_idx = signs.index(0)
        other_indices = [i for i in range(3) if i != zero_idx]
        s1, s2 = signs[other_indices[0]], signs[other_indices[1]]

        # Case 3a: Tangential intersection (both off-plane vertices on same side)
        if s1 == s2:
            return []

        # Case 3b: Transverse crossing cutting through the opposite edge
        i1, i2 = other_indices[0], other_indices[1]
        d1, d2 = d[i1], d[i2]
        t = d1 / (d1 - d2)
        p_cut = verts[i1] + t * (verts[i2] - verts[i1])
        p_zero = verts[zero_idx]
        if np.linalg.norm(p_zero - p_cut) >= epsilon_len_m:
            segments.append((p_zero, p_cut))
        return segments

    # Case 4: No vertices on plane
    if num_zeros == 0:
        # All on the same side: no intersection
        if num_pos == 3 or num_neg == 3:
            return []

        # Standard transverse crossing: one vertex isolated on one side, two on the other
        isolated_idx = 0
        if signs[1] != signs[0] and signs[1] != signs[2]:
            isolated_idx = 1
        elif signs[2] != signs[0] and signs[2] != signs[1]:
            isolated_idx = 2

        other_indices = [i for i in range(3) if i != isolated_idx]
        i0 = isolated_idx
        i1, i2 = other_indices[0], other_indices[1]
        d0, d1, d2 = d[i0], d[i1], d[i2]

        t1 = d0 / (d0 - d1)
        p_cut1 = verts[i0] + t1 * (verts[i1] - verts[i0])

        t2 = d0 / (d0 - d2)
        p_cut2 = verts[i0] + t2 * (verts[i2] - verts[i0])

        if np.linalg.norm(p_cut1 - p_cut2) >= epsilon_len_m:
            segments.append((p_cut1, p_cut2))
        return segments

    return segments


def cluster_endpoints(
    points: np.ndarray,
    tolerance_m: float = EPSILON_SNAP_M,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Clusters 3D endpoints with a strict diameter bound <= tolerance_m.
    
    Prevents transitive clustering from expanding cluster diameter beyond tolerance_m.
    Uses KDTree radius search to avoid artificial cell-boundary splits.
    
    Returns:
    - cluster_ids: np.ndarray of shape (M,) mapping each point index to its cluster index
    - cluster_centroids: np.ndarray of shape (C, 3) with representative coordinates
    """
    points = np.asarray(points, dtype=np.float64)
    M = len(points)
    if M == 0:
        return np.zeros(0, dtype=np.int64), np.zeros((0, 3), dtype=np.float64)

    tree = KDTree(points)
    cluster_ids = np.full(M, -1, dtype=np.int64)
    clusters: List[List[int]] = []

    # Sort indices by coordinates to guarantee deterministic clustering order
    order = np.lexsort((points[:, 0], points[:, 1], points[:, 2]))

    for idx in order:
        if cluster_ids[idx] != -1:
            continue

        # Start a new cluster with point idx
        candidate_cluster = [int(idx)]
        # Query neighbors within tolerance radius
        neighbors = tree.query_ball_point(points[idx], r=tolerance_m)
        # Sort neighbors by distance to current point
        neighbors = [int(n) for n in neighbors if cluster_ids[n] == -1 and n != idx]
        neighbors.sort(key=lambda n: float(np.linalg.norm(points[n] - points[idx])))

        for n in neighbors:
            # Check diameter constraint: distance to all current cluster members <= tolerance_m
            can_add = True
            for member in candidate_cluster:
                if np.linalg.norm(points[n] - points[member]) > tolerance_m:
                    can_add = False
                    break
            if can_add:
                candidate_cluster.append(n)

        cluster_idx = len(clusters)
        for member in candidate_cluster:
            cluster_ids[member] = cluster_idx
        clusters.append(candidate_cluster)

    # Compute centroids for each cluster
    centroids = np.zeros((len(clusters), 3), dtype=np.float64)
    for c_idx, members in enumerate(clusters):
        centroids[c_idx] = np.mean(points[members], axis=0)

    return cluster_ids, centroids


def _segments_intersect_2d(
    p1: np.ndarray, p2: np.ndarray,
    p3: np.ndarray, p4: np.ndarray,
    eps: float = 1e-12,
) -> bool:
    """Returns True if open line segments (p1, p2) and (p3, p4) strictly intersect in 2D."""
    def ccw(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    d1 = ccw(p3, p4, p1)
    d2 = ccw(p3, p4, p2)
    d3 = ccw(p1, p2, p3)
    d4 = ccw(p1, p2, p4)

    if ((d1 > eps and d2 < -eps) or (d1 < -eps and d2 > eps)) and \
       ((d3 > eps and d4 < -eps) or (d3 < -eps and d4 > eps)):
        return True
    return False


def check_self_intersection_2d(points_2d: np.ndarray) -> bool:
    """
    Checks if a closed 2D polygon self-intersects across non-adjacent edges.
    """
    K = len(points_2d)
    if K < 4:
        return False
    for i in range(K):
        a1, a2 = points_2d[i], points_2d[(i + 1) % K]
        # Compare with non-adjacent edges
        for j in range(i + 2, K):
            if i == 0 and j == K - 1:
                continue  # adjacent across wrap-around
            b1, b2 = points_2d[j], points_2d[(j + 1) % K]
            if _segments_intersect_2d(a1, a2, b1, b2):
                return True
    return False


def stitch_segments_into_loops(
    segments: List[Tuple[np.ndarray, np.ndarray]],
    tolerance_m: float = EPSILON_SNAP_M,
) -> List[ContourLoop]:
    """
    Stitches an unordered collection of 3D line segments into ordered, closed ContourLoops.
    
    Enforces:
    1. Bounded-diameter endpoint clustering (diameter <= tolerance_m).
    2. Zero-length segment discarding.
    3. Duplicate and antiparallel segment deduplication.
    4. Deterministic graph construction.
    5. Strict rejection of degree-1 open boundaries (OpenContourError).
    6. Resolution of even higher-degree nodes (e.g. degree 4) via tangent continuity
       or strict rejection if ambiguous / odd degree (NonManifoldContourError).
    7. Closed cycle traversal.
    8. 2D self-intersection detection (SelfIntersectingContourError).
    9. Exact polygon perimeter in meters converted to centimeters.
    """
    if not segments:
        return []

    # Collect and flatten all endpoints
    endpoints_list: List[np.ndarray] = []
    for s_start, s_end in segments:
        endpoints_list.append(np.asarray(s_start, dtype=np.float64))
        endpoints_list.append(np.asarray(s_end, dtype=np.float64))

    all_points = np.vstack(endpoints_list)
    cluster_ids, centroids = cluster_endpoints(all_points, tolerance_m=tolerance_m)

    # Build unique undirected edges
    unique_edges: Set[Tuple[int, int]] = set()
    num_segs = len(segments)
    for s_i in range(num_segs):
        u = int(cluster_ids[2 * s_i])
        v = int(cluster_ids[2 * s_i + 1])
        if u == v:
            # Discard zero-length segment
            continue
        edge = (min(u, v), max(u, v))
        unique_edges.add(edge)

    if not unique_edges:
        return []

    # Build adjacency structure
    adj: Dict[int, Set[int]] = {}
    for u, v in unique_edges:
        adj.setdefault(u, set()).add(v)
        adj.setdefault(v, set()).add(u)

    # Degree validation:
    # 1. First check for non-manifold branching (deg == 3 or deg > 4)
    for node, neighbors in adj.items():
        deg = len(neighbors)
        if deg == 3:
            raise NonManifoldContourError(
                f"Contour has degree-3 branching node at cluster {node}: non-manifold intersection",
                details={"node": node, "neighbors": list(neighbors)},
            )
        if deg > 4:
            raise NonManifoldContourError(
                f"Contour has high-degree node {node} (deg {deg}): non-manifold graph",
                details={"node": node, "degree": deg},
            )

    # 2. Check for open boundary nodes (deg == 1)
    # If any degree-1 nodes exist in a graph without deg >= 3, raise OpenContourError
    has_deg_1 = any(len(neighbors) == 1 for neighbors in adj.values())
    deg4_nodes = [node for node, neighbors in adj.items() if len(neighbors) == 4]

    # If there are open boundaries and no degree-4 nodes to resolve, fail early with OpenContourError
    if has_deg_1 and not deg4_nodes:
        for node, neighbors in adj.items():
            if len(neighbors) == 1:
                raise OpenContourError(
                    f"Contour has degree-1 boundary node at cluster {node}: open contour detected",
                    details={"node": node, "neighbors": list(neighbors)},
                )
    for node in deg4_nodes:
        neighbors = sorted(list(adj[node]))
        c_u = centroids[node]
        t_vecs = []
        for w in neighbors:
            vec = centroids[w] - c_u
            norm = np.linalg.norm(vec)
            if norm < 1e-12:
                raise NonManifoldContourError(f"Degenerate edge length at node {node}")
            t_vecs.append(vec / norm)

        # 3 possible pairings of the 4 neighbors
        pairings = [
            ((0, 1), (2, 3)),
            ((0, 2), (1, 3)),
            ((0, 3), (1, 2)),
        ]

        scored_pairings = []
        for p1, p2 in pairings:
            # For outward pointing vectors, straight continuation means dot product ~ -1.0
            dot1 = float(np.dot(t_vecs[p1[0]], t_vecs[p1[1]]))
            dot2 = float(np.dot(t_vecs[p2[0]], t_vecs[p2[1]]))
            # Error metric: deviation from straight continuation (-1.0)
            err = max(abs(dot1 + 1.0), abs(dot2 + 1.0))
            scored_pairings.append((err, dot1, dot2, p1, p2))

        scored_pairings.sort(key=lambda x: x[0])
        best_err, best_d1, best_d2, best_p1, best_p2 = scored_pairings[0]
        second_err = scored_pairings[1][0]

        # Straight continuation requires dot products <= -0.75 (angle >= 138 deg)
        # and unambiguous margin over alternate pairings
        if best_d1 <= -0.75 and best_d2 <= -0.75 and (second_err - best_err) >= 0.25:
            # Successfully disambiguated: split node into two virtual nodes
            # Remove original node connections
            w_p1 = [neighbors[best_p1[0]], neighbors[best_p1[1]]]
            w_p2 = [neighbors[best_p2[0]], neighbors[best_p2[1]]]

            # Create new split node IDs
            split_node_1 = node
            split_node_2 = len(centroids) + len(deg4_nodes) + 1000 + node

            # Rewire adj
            adj[split_node_1] = set(w_p1)
            for w in w_p1:
                adj[w].remove(node)
                adj[w].add(split_node_1)

            adj[split_node_2] = set(w_p2)
            for w in w_p2:
                adj[w].remove(node)
                adj[w].add(split_node_2)
        else:
            raise NonManifoldContourError(
                f"Degree-4 node {node} has ambiguous tangent continuation (best error {best_err:.3f}, second {second_err:.3f})",
                details={"node": node, "best_dots": (best_d1, best_d2)},
            )

    # 3. Check again for any remaining degree-1 nodes after degree-4 resolution
    for node, neighbors in adj.items():
        if len(neighbors) == 1:
            raise OpenContourError(
                f"Contour has degree-1 boundary node at cluster {node}: open contour detected",
                details={"node": node, "neighbors": list(neighbors)},
            )

    # Traverse closed 2-regular cycles
    visited_nodes: Set[int] = set()
    extracted_loops: List[ContourLoop] = []

    # Sort all active nodes deterministically by coordinates
    def node_sort_key(n: int) -> Tuple[float, float, float]:
        idx_c = n if n < len(centroids) else (n % 1000)
        c = centroids[idx_c]
        return (float(c[2]), float(c[1]), float(c[0]))

    active_nodes = sorted(list(adj.keys()), key=node_sort_key)

    for start_node in active_nodes:
        if start_node in visited_nodes:
            continue
        if len(adj[start_node]) != 2:
            raise NonManifoldContourError(f"Node {start_node} has non-manifold degree {len(adj[start_node])}")

        cycle_nodes: List[int] = [start_node]
        visited_nodes.add(start_node)

        # Deterministically select first neighbor (lowest sort key)
        neighbors = sorted(list(adj[start_node]), key=node_sort_key)
        prev_node = start_node
        curr_node = neighbors[0]

        while curr_node != start_node:
            cycle_nodes.append(curr_node)
            visited_nodes.add(curr_node)

            curr_neighbors = list(adj[curr_node])
            if len(curr_neighbors) != 2:
                raise NonManifoldContourError(f"Cycle encountered non-manifold node {curr_node}")

            next_candidates = [n for n in curr_neighbors if n != prev_node]
            if not next_candidates:
                raise UnclosedContourError(f"Cycle dead-end at node {curr_node}")

            prev_node = curr_node
            curr_node = next_candidates[0]

        # Closed cycle formed
        if len(cycle_nodes) < 3:
            # Degenerate 2-vertex cycle
            continue

        # Extract 3D points
        pts_3d = np.array([
            centroids[n if n < len(centroids) else (n % 1000)]
            for n in cycle_nodes
        ], dtype=np.float64)

        # Self-intersection check: project to best-fit 2D plane
        # Center points
        centroid = np.mean(pts_3d, axis=0)
        centered = pts_3d - centroid
        # Normal via SVD
        _, _, vh = np.linalg.svd(centered)
        # Normal is least singular vector
        plane_normal = vh[2]
        # Basis vectors in plane
        u_axis = vh[0]
        v_axis = vh[1]
        pts_2d = np.column_stack([np.dot(centered, u_axis), np.dot(centered, v_axis)])

        if check_self_intersection_2d(pts_2d):
            raise SelfIntersectingContourError(
                "Extracted loop self-intersects in planar coordinates",
                details={"vertex_count": len(pts_3d)},
            )

        # Compute 3D Euclidean perimeter
        k_pts = len(pts_3d)
        perim_m = sum(float(np.linalg.norm(pts_3d[(i + 1) % k_pts] - pts_3d[i])) for i in range(k_pts))
        perim_cm = perim_m * 100.0

        bb_min = (float(pts_3d[:, 0].min()), float(pts_3d[:, 1].min()), float(pts_3d[:, 2].min()))
        bb_max = (float(pts_3d[:, 0].max()), float(pts_3d[:, 1].max()), float(pts_3d[:, 2].max()))
        centroid_tuple = (float(centroid[0]), float(centroid[1]), float(centroid[2]))

        extracted_loops.append(ContourLoop(
            points_3d_m=pts_3d,
            is_closed=True,
            centroid_3d_m=centroid_tuple,
            bounding_box_min_m=bb_min,
            bounding_box_max_m=bb_max,
            perimeter_cm=float(perim_cm),
        ))

    return extracted_loops
