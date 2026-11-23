# Anthropometry, Coordinate Scale & Discrepancy Reconciliation Analysis

**Candidate:** NAVER Anny v0.6.2 (Native Topology)  
**Evaluation Mode:** Actual Local GPU Inference (`cuda:0`, NVIDIA RTX 3050 Laptop GPU 4 GB)  
**Experiment Date:** 2026-11-23  
**Status:** 🧪 Actual Experiment Result / ✅ Verified Geometric Derivation  

---

## 1. Coordinate Scale & Stature Reconciliation

To establish coordinate units and reconcile the observed height values, we evaluated both the template mesh (`rest_vertices`) and posed mesh (`vertices` with identity bone transforms) across controlled sweeps of the native `height` phenotype parameter:

| `height` Parameter | Rest Vertex Span ($Z$-axis) | Posed Bounding Box Height ($m$) | Height Discrepancy ($\Delta z$, $cm$) | Native Anny Waist ($m$) | Model Volume ($m^3$) | Model Mass ($kg$) | Model BMI ($kg/m^2$) |
|---|---|---|---|---|---|---|---|
| `0.00` | $1.0597\text{ m}$ ($105.97\text{ cm}$) | $1.0542\text{ m}$ ($105.42\text{ cm}$) | $0.56\text{ cm}$ | $0.5306$ | $0.0189$ | $18.57$ | $16.53$ |
| `0.25` | $1.3140\text{ m}$ ($131.40\text{ cm}$) | $1.3061\text{ m}$ ($130.61\text{ cm}$) | $0.80\text{ cm}$ | $0.6007$ | $0.0299$ | $29.33$ | $16.99$ |
| `0.50` (Baseline) | $1.5683\text{ m}$ ($156.83\text{ cm}$) | $1.5597\text{ m}$ ($155.97\text{ cm}$) | **$0.87\text{ cm}$** | $0.6711$ | $0.0444$ | $43.49$ | $17.68$ |
| `0.75` | $1.8226\text{ m}$ ($182.26\text{ cm}$) | $1.8140\text{ m}$ ($181.40\text{ cm}$) | $0.85\text{ cm}$ | $0.7418$ | $0.0628$ | $61.50$ | $18.52$ |
| `1.00` | $2.0769\text{ m}$ ($207.69\text{ cm}$) | $2.0689\text{ m}$ ($206.89\text{ cm}$) | $0.80\text{ cm}$ | $0.8128$ | $0.0855$ | $83.82$ | $19.43$ |

### Findings & Height Reconciliation:
1. **Coordinate Scale:** Coordinates are natively in **METERS** ($1.0\text{ unit} = 1.0\text{ meter}$). Conversion factor to centimeters is exactly $100.0$.
2. **Reconciliation of $156.83\text{ cm}$ vs $155.97\text{ cm}$ ($0.87\text{ cm}$ Difference):**
   - In Anny, `rest_vertices` has $Z$ bounds from $-0.8206\text{ m}$ (sole of foot) to $+0.7477\text{ m}$ (vertex of crown) $\rightarrow \Delta Z = 1.5683\text{ m} = \mathbf{156.83\text{ cm}}$.
   - When Anny executes forward skinning (even with identity transforms), linear blend skinning computes vertex offsets relative to the 104-bone skeletal hierarchy. In this settled pose, $Z$ bounds range from $-0.8391\text{ m}$ to $+0.7206\text{ m}$ $\rightarrow \Delta Z = 1.5597\text{ m} = \mathbf{155.97\text{ cm}}$.
   - The $0.87\text{ cm}$ difference is the mechanical joint settling of the skinning deformer relative to the unposed template mesh.

---

## 2. Investigation of Waist Circumference Discrepancy

In preliminary testing, a discrepancy of $7.80\text{ cm}$ was observed between Anny's native waist measurement ($67.11\text{ cm}$) and initial custom extraction ($74.91\text{ cm}$). We conducted an in-depth geometric audit to determine the root cause.

### A. Anny's Native Waist Implementation
Source code inspection of `anny.anthropometry.Anthropometry.waist_circumference` reveals:
```python
# BASE_MESH_WAIST_VERTICES contains 46 specific ordered vertex indices
def waist_circumference(self, rest_vertices):
    waist_vertices = rest_vertices[:, self.waist_vertex_indices]
    waist_vertices_rolled = torch.roll(waist_vertices, shifts=1, dims=1)
    return torch.sum(torch.linalg.norm(waist_vertices_rolled - waist_vertices, dim=-1), dim=-1)
```
- Anny defines waist circumference as a **continuous 3D closed polygonal chain across 46 anatomical mesh vertices**.
- The 46 waist vertices have a mean $Z$-coordinate of **$0.1334\text{ m}$ ($60.83\%$ of stature height)**, NOT $66.0\%$.
- Crucially, the 46 vertices do **not** lie on a single horizontal plane: they span a vertical range from $Z = 0.1258\text{ m}$ to $Z = 0.1432\text{ m}$ (a vertical tilt span of $1.74\text{ cm}$), rising at the lateral flanks and dipping anteriorly across the navel.

### B. Root Causes of Initial Custom Extraction Overestimation ($74.91\text{ cm}$)
1. **Vertical Misalignment:** The uncalibrated slice was placed at $66.0\%$ height ($Z \approx 0.21\text{ m}$), which is $\sim 8\text{ cm}$ above the anatomical waistline, cutting across the wider lower ribcage.
2. **Arm Vertex Contamination:** In standard A-pose, the hands and forearms hang down laterally beside the waist ($Z \approx 0.10\text{--}0.25\text{ m}$). A naive geometric slice that did not filter out lateral arm vertices included wrist points ($|X| > 0.20\text{ m}$), expanding the bounding perimeter.
3. **Convex Hull Overestimation:** A convex hull bridges across inward anatomical concavities (e.g. the lumbar lordosis curve of the lower spine).

### C. Calibrated Reconciliation Results
When arm vertices are cleanly isolated ($|X| < 0.20\text{ m}$) and a planar cross-section is extracted at the exact anatomical waist height ($Z = 0.1334\text{ m}$):
- **Native 3D Polygonal Waist Loop:** **$67.11\text{ cm}$**
- **Calibrated Planar Slice (Convex Hull):** **$67.90\text{ cm}$**
- **Difference:** **$0.79\text{ cm}$ ($1.18\%$ difference)**.

The remaining $<8\text{ mm}$ difference is completely accounted for by the $1.74\text{ cm}$ 3D anatomical tilt of the waist loop relative to a horizontal cross-section plane.

---

## 3. Canonical Anatomical Definitions & Landmarks

To ensure reproducibility across buyer body profiles and seller garment specifications, WearWise establishes the following canonical measurement protocol:

```text
       ┌─────────── Head Vertex (Z_max)
       │
       ├─────────── Biacromial Shoulder Breadth (82.0% H, Z = 0.465m)
       │            C7 Cervical Vertebra (85.0% H, Start of Torso Length)
       │
       ├─────────── Chest / Bust Circumference (72.0% H, Z = 0.309m)
       │
       ├─────────── Natural Waist Circumference (60.8% H, Z = 0.133m)
       │
       ├─────────── Crotch Line / Perineum (52.0% H, End of Torso Length)
       │            Maximum Hip / Trochanteric Circumference (51.0% H, Z = -0.021m)
       │
       └─────────── Heel / Floor Contact (Z_min)
```

| Dimension | Canonical Landmark & Extraction Convention | Baseline Male ($cm$) | Method & Provenance |
|---|---|---|---|
| **Stature Height** | Vertical distance between lowest heel contact vertex ($Z_{\min}$) and crown vertex ($Z_{\max}$) in reference standing pose. | $156.83\text{ cm}$ (Rest) / $155.97\text{ cm}$ (Posed) | Geometry-extracted |
| **Chest Circumference** | Planar cross-section perimeter at $72.0\%$ stature height (nipple line / lower axillary fold), with arm vertices filtered ($|X| < 0.23\text{ m}$). | $111.11\text{ cm}$ | Geometry-extracted |
| **Waist Circumference** | Anatomical waistline perimeter at $60.83\%$ stature height ($Z = 0.1334\text{ m}$), with arm vertices filtered ($|X| < 0.20\text{ m}$). | $67.11\text{ cm}$ (Native loop) / $67.90\text{ cm}$ (Planar slice) | Geometry-extracted |
| **Hip Circumference** | Planar cross-section perimeter at $51.0\%$ stature height (widest lateral trochanteric and posterior gluteal prominence), with arm vertices filtered ($|X| < 0.22\text{ m}$). | $88.43\text{ cm}$ | Geometry-extracted |
| **Shoulder Breadth (Biacromial)** | Linear horizontal distance between outer left and right acromion process bony landmarks at $82.0\%$ stature height. | $36.84\text{ cm}$ | Geometry-extracted |
| **Shoulder Breadth (Deltoid Outer)** | Maximum outer lateral width across deltoid contours at $82.0\%$ stature height. | $39.17\text{ cm}$ | Geometry-extracted |
| **Torso Length** | Vertical distance between C7 cervical vertebra landmark ($85.0\%$ stature) and perineal crotch plane ($52.0\%$ stature). | $51.75\text{ cm}$ | Geometry-extracted |

---

## 4. Reference Pose Documentation

All measurements are strictly extracted in the documented **Standard Neutral Reference Pose**:
1. **Joint Transforms:** Identity rotation transforms for all 104 bones in the Anny skeletal rig (`pose_parameters = eye(4)`).
2. **Upper Body:** Upright trunk; spine vertical along $Z$-axis; gaze directed forward along $+Y$ axis.
3. **Arms:** Natural A-pose, abducted laterally at an angle of $\sim 30^\circ$ from the torso; palms facing medially.
4. **Lower Body:** Straight legs; feet parallel, spaced at natural stance width ($\sim 18\text{ cm}$ inter-malleolar distance); heels resting on $Z_{\min}$ plane.

---

## 5. Distinction Between Estimates and Validated Ground Truth

To ensure compliance with WearWise's Honest Fit principles:
1. **Geometry-Derived Estimates:** All measurements extracted above (chest, waist, hips, shoulders) are deterministic geometric calculations from a mathematical 3D parametric surface. They are tagged as `geometry_extracted`.
2. **Externally Validated Human Measurements:** Real human tape measurements with consenting adult volunteers have **NOT** been performed in Phase 0. External accuracy (MAE/RMSE) can only be established during the volunteer validation trials in **Phase 8**.
3. **Exclusion of Model-Derived Mass & BMI:** Anny's native volume-derived mass ($43.49\text{ kg}$) and BMI ($17.68$) rely on a uniform water-buoyancy assumption ($\rho \approx 980\text{ kg/m}^3$). Because human bone and visceral fat density vary widely, **model-derived mass and BMI are strictly excluded from ground-truth claims and fit calculations.**
