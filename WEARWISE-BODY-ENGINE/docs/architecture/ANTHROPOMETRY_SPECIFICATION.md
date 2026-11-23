# WearWise Anthropometry Engine & Measurement Specification

**Project:** WearWise AI Fashion & Honest Fit Platform  
**Document:** Anthropometry Specification (ANT-001)  
**Revision:** 1.2 (Exact Mesh-Plane Intersection, Graph Stitching & Landmark Disambiguation)  
**Date:** 2026-11-23  
**Status:** Approved Technical Architecture  

---

## 1. Scope, Coordinate Standards & Model Boundaries

This specification establishes the canonical anthropometric measurement dictionary, coordinate system standards, reference landmarks, and exact geometric intersection algorithms for the WearWise platform.

### Core Architecture & Boundaries:
- **Apparel Sizing Focus:** Definitions are optimized for clothing fit intelligence (tailoring ease, collar/chest/waist/hip room, inseams), **NOT** for orthopedic or clinical diagnosis.
- **Model-Derived Geometric Estimates:** Measurements extracted from the 3D avatar mesh are geometric calculations over surface vertices. They are mathematically deterministic but must **never be represented as externally verified human ground truth** until calibrated against live human subjects in Phase 8.
- **Specification Status:** The exact mesh-plane intersection algorithm specified herein is an **architectural contract** designed to replace Phase 0 convex-hull heuristics. In strict compliance with Phase 1 boundaries, it has **not yet been implemented or experimentally validated**. Implementation and unit/property testing will occur in **Phase 4**.
- **Metric Standards:** Coordinate values in 3D geometry are strictly in **METERS ($m$)**. All domain entities, REST APIs, and database tables store dimensions in **CENTIMETERS ($cm$)** using the exact conversion:
  $$\text{value}_{\text{cm}} = \text{value}_{\text{m}} \times 100.0$$
- **Right-Handed Coordinate Axes:** $+X$ = Lateral Left-to-Right; $+Y$ = Posterior-to-Anterior (Forward); $+Z$ = Plantar-to-Cranial (Vertical / Upward).
- **Reference Pose:** Standard Neutral A-Pose (upright, feet resting at $Z \approx -0.839\text{ m}$, head facing $+Y$, arms abducted downward $\sim 30^\circ$ from torso in coronal plane).

---

## 2. Canonical Measurement Dictionary & Historical Evidence

The table below preserves the exact empirical Phase 0 benchmark values on the neutral baseline male mannequin while formally documenting landmark conventions, plane orientations, loop selection rules, and validation states:

| Measurement Code | Common Name | Reference Landmark & Slicing Plane | Loop Selection Rule | Baseline Value (Phase 0) | Validation State |
|---|---|---|---|---|---|
| `stature` | Total Height | Vertical distance from lowest plantar vertex ($Z_{\min}$) to crown vertex ($Z_{\max}$) | Bounding Box $Z$-extent | **$156.83\text{ cm}$** (Template)<br>**$155.97\text{ cm}$** (Posed LBS) | Validated (Model) |
| `chest_circumference` | Chest / Bust Girth | Transverse plane at $72\%$ stature ($Z \approx 0.29\text{ m}$), intersecting bust/nipple apex | Nearest loop to `sternum_lower` landmark | **$111.11\text{ cm}$** | Validated (Model) |
| `chest_high_axillary_circumference` | High Axillary Chest | Transverse plane at $76\%$ stature ($Z \approx 0.35\text{ m}$), through upper axillary armpit folds | Central torso loop; arms excluded via region mask | **$111.73\text{ cm}$** | Provisional |
| `waist_natural_circumference` | Natural Waist (3D) | 3D geodesic surface loop passing through natural waist indentation ($60.83\%$ stature, $Z \approx 0.133\text{ m}$) | Native 3D loop provided via `LandmarkProvider` | **$67.11\text{ cm}$** | Validated (Native Anny) |
| `waist_planar_circumference` | Planar Torso Waist | Transverse plane at natural waist height ($Z = 0.1334\text{ m}$) | Nearest loop to `umbilicus` landmark | **$67.90\text{ cm}$** | Validated (Model) |
| `hip_circumference` | Hip / Seat Girth | Transverse plane at $51\%$ stature ($Z \approx -0.04\text{ m}$), through maximal greater trochanters and gluteal apex | Nearest loop to `sacrum_mid` landmark | **$88.43\text{ cm}$** | **Provisional** |
| `shoulder_biacromial_breadth` | Biacromial Breadth | Euclidean distance between left and right lateral acromial processes of scapula | Landmark pair: `acromion_left` to `acromion_right` ($|Y| \le 0.05\text{ m}$) | **$36.84\text{ cm}$** | Validated (Model) |
| `shoulder_deltoid_outer_breadth` | Outer Shoulder Width | Transverse slab at $82\%$ stature ($Z \approx 0.45\text{ m}$); maximum lateral $X$-span | Lateral extrema across deltoid muscle contours | **$39.17\text{ cm}$** | Validated (Model) |
| `torso_length` | Torso Length | Vertical distance along dorsal spine from C7 cervical vertebra to perineum (crotch level) | Landmark delta: $Z(\text{C7}) - Z(\text{perineum})$ | **$51.75\text{ cm}$** | Validated (Model) |
| `arm_bicep_circumference` | Upper Arm Girth | Plane perpendicular to humerus bone axis at maximal bicep belly | Single loop enclosing left or right upper arm segment | Uncalibrated | Provisional |
| `leg_thigh_circumference` | Thigh Girth | Plane perpendicular to femur bone axis $3\text{ cm}$ below inferior gluteal fold | Single loop enclosing isolated upper leg segment | Uncalibrated | Provisional |
| `leg_calf_circumference` | Calf Girth | Transverse plane at $28\%$ stature through maximal gastrocnemius belly | Single loop enclosing isolated lower leg segment | Uncalibrated | Provisional |

---

## 3. Exact Triangle-Mesh-Plane Intersection Algorithm Specification

The naive Z-slab and 2D convex hull heuristic used during early Phase 0 experiments is formally replaced by the **Exact Triangle-Mesh-Plane Intersection Algorithm** (`algorithm_version: 1.2-mesh-plane-graph`):

```mermaid
flowchart TD
    MeshInput["1. MeshData (Vertices & Triangular Faces) + Cutting Plane (n, d)"] --> FaceFilter
    FaceFilter["2. Filter Degenerate Faces & Signed Distance Evaluation<br>d_i = (v_i - p) . n"] --> EdgeCrossing
    EdgeCrossing["3. Identify Edge-Plane Crossings & Handle Edge Cases<br>(Coplanar faces/edges, on-plane vertices, tangential touches)"] --> SegGraph
    SegGraph["4. Spatial Hash Deduplication & Graph Construction<br>Nodes = quantized points; Edges = intersection segments"] --> DegCheck
    DegCheck{"5. Graph Degree Validation<br>Are all nodes 2-regular (degree == 2)?"}
    DegCheck -->|Yes| LoopStitch["6. Stitch Segments into Directed Closed Loops"]
    DegCheck -->|No| ManifoldDisambig["Disambiguate Non-Manifold Nodes or Reject"]
    LoopStitch --> LandmarkFilter["7. Landmark-Guided Proximity Selection<br>(Select loop closest to anatomical landmark axis)"]
    LandmarkFilter --> CalcPerim["8. Calculate Exact 3D Polygon Perimeter<br>Sum Euclidean distances along stitched loop"]
    CalcPerim --> Output["9. Return Result (cm) + Diagnostic Record"]
```

### 3.1 Edge-Case & Geometric Robustness Rules

The intersection algorithm must handle all topological singularities deterministically:

1. **Numerical Epsilon ($\epsilon = 10^{-6}\text{ m}$):** Any vertex with $|d_i| \le \epsilon$ is treated as lying **exactly on the plane**.
2. **Coplanar Triangles (All 3 Vertices on Plane):**
   - If $|d_0| \le \epsilon$, $|d_1| \le \epsilon$, and $|d_2| \le \epsilon$, the entire triangle is coplanar with the plane.
   - **Handling Rule:** The face is discarded from intersection segment generation. Its boundary edges will be generated by intersecting neighboring non-coplanar faces, preventing interior surface fill artifacts.
3. **Coplanar Edges (2 Vertices on Plane, 1 Off-Plane):**
   - If $|d_0| \le \epsilon$ and $|d_1| \le \epsilon$, while $|d_2| > \epsilon$, the edge $(v_0, v_1)$ lies on the plane.
   - **Handling Rule:** Generate a line segment between $v_0$ and $v_1$. To prevent duplicate segments generated by the adjacent sharing face, canonical edge hashing ($\min(i, j), \max(i, j)$) is enforced.
4. **Tangential Intersections (1 Vertex on Plane, 2 Vertices on Same Side):**
   - If $|d_0| \le \epsilon$ and $\text{sign}(d_1) == \text{sign}(d_2) \neq 0$, the plane touches the triangle at a single vertex without cutting across it.
   - **Handling Rule:** Discard; touches without crossing produce zero-length segments and must not enter the graph.
5. **Transverse Crossing (1 Vertex on One Side, 2 on the Other):**
   - Standard cutting case. Intersect edge $(v_0, v_1)$ and edge $(v_0, v_2)$ with plane:
     $$t = \frac{d_0}{d_0 - d_j}, \quad \mathbf{p}_{\text{int}} = v_0 + t (v_j - v_0)$$
   - Generate segment between the two intersection points.
6. **Degenerate Faces:** Faces with zero cross-product normal area ($\|(\mathbf{v}_1 - \mathbf{v}_0) \times (\mathbf{v}_2 - \mathbf{v}_0)\| \le 10^{-12}$) are stripped during preprocessing.

### 3.2 Graph-Based Segment Stitching & Degree-2 Validation

```python
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class ContourLoop:
    """An ordered, closed 3D polygonal loop on the mesh surface."""
    points_3d_m: np.ndarray       # Shape (K, 3), coordinates in METERS
    is_closed: bool               # True if start and end points meet within tolerance
    centroid_3d_m: List[float]    # (Xc, Yc, Zc) centroid of loop
    bounding_box_min_m: List[float]
    bounding_box_max_m: List[float]
    perimeter_cm: float

@dataclass(frozen=True)
class ExtractionDiagnostic:
    """Diagnostic metadata for measurement extraction."""
    algorithm_version: str        # "1.2-mesh-plane-graph"
    plane_origin_m: List[float]
    plane_normal: List[float]
    intersected_triangles_count: int
    extracted_loops_count: int
    selected_loop_index: int
    closure_error_m: float
    graph_is_2_regular: bool
    is_plausible: bool

def stitch_segments_into_loops(
    segments: List[Tuple[np.ndarray, np.ndarray]], 
    tolerance_m: float = 1e-6
) -> List[ContourLoop]:
    """
    Constructs an adjacency graph using spatial quantization hashing.
    Validates that nodes have degree == 2, and traverses edges to form closed loops.
    """
    # 1. Spatial hash to quantize endpoints and merge duplicate vertices
    # 2. Build adjacency list: node -> List[neighbor_nodes]
    # 3. Check graph degree: valid manifold loops require degree == 2 for all visited nodes
    # 4. Traverse adjacency graph from unvisited node until loop closes
    # 5. Calculate 3D Euclidean perimeter: sum(||p_i - p_{i+1}||) * 100.0 cm
    ...
```

### 3.3 Landmark-Guided Proximity Loop Selection

When cutting horizontally across the human body, the plane typically extracts **multiple disconnected closed loops** (e.g. at chest/waist level: 1 central torso loop + 2 arm loops; at thigh level: 2 leg loops).

Universal coordinate thresholds (such as fixed $|X_c| \le 0.20\text{ m}$) are brittle across extreme phenotypes. The engine applies **Landmark-Guided Centroid Proximity**:
1. The `LandmarkProvider` supplies the 3D coordinate of the designated anatomical axis landmark $\mathbf{p}_{\text{landmark}}$ (e.g. `sternum_lower` for chest, `umbilicus` for waist, `sacrum_mid` for hips).
2. For each extracted closed loop $L_j$, compute its 3D centroid $\mathbf{c}_j = \frac{1}{K} \sum_{k=1}^K \mathbf{p}_k$.
3. Compute the horizontal planar Euclidean distance to the landmark:
   $$D(L_j) = \sqrt{(c_{j, x} - p_{\text{landmark}, x})^2 + (c_{j, y} - p_{\text{landmark}, y})^2}$$
4. The loop with the **minimum horizontal distance $D(L_j)$** is selected as the target torso loop. Arm loops have significantly larger centroid deviations and are rejected cleanly.

---

## 4. Landmark Abstraction: The `LandmarkProvider` Protocol

To guarantee that the Anthropometry Engine never couples to Anny's internal vertex numbering, landmark positions are resolved through the engine-neutral `LandmarkProvider` interface:

```python
class LandmarkProvider(Protocol):
    """Supplies 3D landmark points and anatomical vertex masks without exposing engine topology."""
    def get_landmark_point_m(self, landmark_code: str) -> np.ndarray:
        """Returns 3D (X, Y, Z) landmark point in METERS in current mesh pose."""
        ...
        
    def get_region_mask(self, region_code: str) -> np.ndarray:
        """Returns boolean mask of faces/vertices belonging to specified anatomical zone."""
        ...
```

The concrete `AnnyLandmarkProvider` in `app/avatar_engine/adapters/anny_adapter.py` maps internal vertex indices to this public interface.

---

## 5. Explicit Measurement Failure States & Diagnostic Reporting

When measurement extraction fails (e.g. unclosed loop, self-intersection, or non-manifold edge), the Anthropometry Engine **never substitutes a bounding-box approximation**. Instead, it records an explicit status and diagnostic record:

| Extraction Status | Condition | Handling Policy |
|---|---|---|
| `ACTIVE` | Clean closed loop; closure error $< 10^{-6}\text{ m}$; plausible dimensions | Recorded as valid active measurement |
| `PROVISIONAL` | Clean closed loop; provisional tailoring landmark (e.g. hip transverse plane) | Recorded with `status: provisional` |
| `UNASSESSED` | Anatomical region not covered by available landmarks | Flagged as `unassessed`; ignored by fit engine |
| `REJECTED` | Unclosed segment chain; node degree $\neq 2$; self-intersection | Flagged as `status: rejected`; error reason logged in diagnostic metadata |
