# WearWise Phase 0 Open Items, Anthropometric Discrepancy Reconciliation & Evidence Boundaries

**Project:** WearWise AI Fashion & Honest Fit Platform  
**Document:** Architectural Evidence Audit & Boundary Definition  
**Revision:** 1.2 (Empirical Evidence Rigor, RMSR/PVSR Separation & Provisional Bounds)  
**Date:** 2026-11-23  
**Status:** Approved Technical Reconciliation Record  

---

## 1. Executive Purpose

This document performs an exhaustive audit of conflicting figures, extraction conventions, and spillover formulas identified across Phase 0 research records. 

Rather than silently averaging conflicting figures or carrying ambiguity into canonical domain models, this document inspects the raw experimental evidence in [`experiments/outputs/`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/experiments/outputs/) and the extraction code in [`experiments/anny/`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/experiments/anny/). Each discrepancy is resolved, given an approved definition, or explicitly classified as **provisional**, establishing rigorous boundary conditions for all Phase 1 domain schemas.

---

## 2. Anthropometric Discrepancy Register

### Item 1: Hip Circumference ($113.82\text{ cm}$ vs $88.43\text{ cm}$)

| Attribute | Record A | Record B |
|---|---|---|
| **Reported Value** | $113.82\text{ cm}$ | $88.43\text{ cm}$ |
| **Landmark Height** | $56\%$ stature ($Z \approx 0.03\text{ m}$) | $51\%$ stature ($Z \approx -0.04\text{ m}$) |
| **Source Documents** | `PHASE_0_RESEARCH_REPORT.md` (Line 64), early extraction drafts | `experiments/outputs/exp_c_anthropometry.json` (Line 109), `ANTHROPOMETRY_ANALYSIS.md` |
| **Extraction Code** | Naive planar convex hull slice across full $X$-$Y$ plane | `experiments/anny/exp_c_anthropometry.py` (Line 94, 113) with lateral bounding |

#### Investigation & Raw Evidence:
- **Code Inspection:** In `experiments/anny/exp_c_anthropometry.py`:
  ```python
  hip_z = z_min + 0.51 * tot_h
  "hip_circumference_cm": slice_contour(hip_z, max_lateral_x=0.22)
  ```
- **Finding:** In early exploratory slicing, a horizontal cut was taken at $56\%$ stature without constraining lateral $X$ extents. Because Anny's neutral A-pose has hands and wrists extending downward near the upper trochanter, the unconstrained 2D convex hull enclosed both the pelvic contour and lateral forearm/wrist points ($|X| > 0.22\text{ m}$), creating an artificial $+25.39\text{ cm}$ overinflation ($113.82\text{ cm}$).
- When sliced at true anatomical hip/trochanter height ($51\%$ stature) with lateral limb bounding ($|X| \le 0.22\text{ m}$), the planar convex hull perimeter yields **$88.43\text{ cm}$**.
- **Resolution Status:** **Resolved in code, but marked PROVISIONAL in schema.**
- **Approved Definition for Phase 1:**
  - Measurement Code: `hip_circumference`
  - Canonical Baseline Value: **$88.43\text{ cm}$** (on baseline male template, stature $156.83\text{ cm}$).
  - Extraction Method: `planar_convex_hull_bounded` at $51\%$ stature, $|X| \le 0.22\text{ m}$.
  - Assessment State: `provisional` (pending Phase 4 exact mesh-plane loop stitching and geodesic surface loop validation).
- **Architectural Consequence:** The domain schema must not mark hip circumference as `eligible` without qualification. It is typed with `assessment_state: provisional` and acquisition method `geometry_extracted`.

---

### Item 2: Shoulder Breadth ($44.20\text{ cm}$ vs $36.84\text{ cm}$ biacromial vs $39.17\text{ cm}$ deltoid)

| Attribute | Record A | Record B (Biacromial) | Record C (Deltoid Outer) |
|---|---|---|---|
| **Reported Value** | $44.20\text{ cm}$ | $36.84\text{ cm}$ | $39.17\text{ cm}$ |
| **Landmark** | Global lateral extent at $83\%$ stature | Bony acromion landmarks ($|Y| < 0.05\text{ m}$) | Maximum deltoid outer muscle contour |
| **Source Documents** | `PHASE_0_RESEARCH_REPORT.md` (Line 65) | `exp_c_anthropometry.json` (Line 110) | `exp_c_anthropometry.json` (Line 111) |
| **Extraction Code** | Unconstrained slice across $Z \approx 0.45\text{ m}$ | `exp_c_anthropometry.py` (Lines 98–100) | `exp_c_anthropometry.py` (Lines 103–105) |

#### Investigation & Raw Evidence:
- **Code Inspection:**
  ```python
  shoulder_z = z_min + 0.82 * tot_h
  sh_mask = (np.abs(verts_np[:, 2] - shoulder_z) < (0.015 * tot_h)) & (np.abs(verts_np[:, 1]) < 0.05)
  biacromial_cm = float((sh_pts[:, 0].max() - sh_pts[:, 0].min()) * to_cm_factor)  # 36.84 cm
  
  deltoid_mask = np.abs(verts_np[:, 2] - shoulder_z) < (0.02 * tot_h)
  deltoid_breadth_cm = float((deltoid_pts[:, 0].max() - deltoid_pts[:, 0].min()) * to_cm_factor)  # 39.17 cm
  ```
- **Finding:** The $44.20\text{ cm}$ figure was derived from an unconstrained horizontal bounding box at $83\%$ stature, which captured the lateral flare of the abducted upper arms. Calibrated extraction accurately distinguishes between:
  1. **Biacromial Breadth ($36.84\text{ cm}$):** Distance between the bony acromial processes of the scapulae (standard tailoring landmark for shirt yoke and shoulder seam placement).
  2. **Deltoid Outer Breadth ($39.17\text{ cm}$):** Maximum horizontal span across the outer contours of the deltoid muscles (used for jacket outer shoulder fit).
- **Resolution Status:** **Fully Resolved by Disambiguation.**
- **Approved Definitions for Phase 1:**
  - Measurement Code 1: `shoulder_biacromial_breadth` $\rightarrow$ Baseline value: **$36.84\text{ cm}$**; definition: distance between lateral edges of acromial processes ($|Y| \le 0.05\text{ m}$ at $82\%$ stature).
  - Measurement Code 2: `shoulder_deltoid_outer_breadth` $\rightarrow$ Baseline value: **$39.17\text{ cm}$**; definition: maximum lateral distance across outer deltoid contours at $82\%$ stature.
  - The ambiguous generic term "shoulder breadth" ($44.20\text{ cm}$) is **formally retired and forbidden**.

---

### Item 3: Chest Circumference ($111.73\text{ cm}$ vs $111.11\text{ cm}$)

| Attribute | Record A | Record B |
|---|---|---|
| **Reported Value** | $111.73\text{ cm}$ | $111.11\text{ cm}$ |
| **Landmark Height** | $76\%$ stature ($Z \approx 0.35\text{ m}$) | $72\%$ stature ($Z \approx 0.29\text{ m}$) |
| **Source Documents** | `PHASE_0_RESEARCH_REPORT.md` (Line 63) | `experiments/outputs/exp_c_anthropometry.json` (Line 107) |
| **Extraction Code** | Slice at high axillary fold level | `experiments/anny/exp_c_anthropometry.py` (Line 92, 111) |

#### Investigation & Raw Evidence:
- **Code Inspection:**
  ```python
  chest_z = z_min + 0.72 * tot_h
  "chest_circumference_cm": slice_contour(chest_z, max_lateral_x=0.23)
  ```
- **Finding:** A vertical gradient exists across the human thoracic cage. Slicing at $76\%$ stature measures the **high axillary line** ($111.73\text{ cm}$). Slicing at $72\%$ stature passes directly through the **nipple/bust apex** ($111.11\text{ cm}$). The difference is $0.62\text{ cm}$ ($0.55\%$), representing normal anatomical torso taper.
- **Resolution Status:** **Fully Resolved as Landmark Specificity.**
- **Approved Definition for Phase 1:**
  - Canonical Code: `chest_circumference` $\rightarrow$ Baseline: **$111.11\text{ cm}$** ($72\%$ stature).
  - Secondary Code: `chest_high_axillary_circumference` $\rightarrow$ Baseline: **$111.73\text{ cm}$** ($76\%$ stature).

---

### Item 4: Parameter Spillover Metrics & Bound Evidence

| Metric Name | Mathematical Definition | Historical Status in Phase 0 | Architectural Role in Phase 1 |
|---|---|---|---|
| **Regional Mean Spillover Ratio (RMSR)** | $\text{RMSR}_R(p) = \frac{\bar{\Delta}_R(p)}{\bar{\Delta}_{R_{\text{target}}}(p) + \epsilon}$ | **Empirically Measured** in `exp_b_parameter_behaviour.py` across 20 parameters. | Primary metric in `ShapeEvaluationPort` and BICE loss $\mathcal{L}_{\text{locality}}$. |
| **Peak Vertex Spillover Ratio (PVSR)** | $\text{PVSR}(p) = \frac{\max_{v \notin \mathcal{R}_{\text{target}}} \|\Delta \mathbf{x}_v\|}{\max_{v \in \mathcal{R}_{\text{target}}} \|\Delta \mathbf{x}_v\| + \epsilon}$ | Formulated mathematically in reports; **NOT empirically logged for all vertices** in Phase 0 JSON. | Secondary metric reserved for vertex-level boundary testing in Phase 3. |

#### Investigation & Clarifications:
- **Historical Implementation:** `experiments/anny/exp_b_parameter_behaviour.py` (lines 274–278) computed **RMSR**:
  ```python
  t_disp = mod_res["regional_means"].get(target_r, 0.0)
  other_disps = [v for k, v in mod_res["regional_means"].items() if k != target_r]
  max_other = max(other_disps) if other_disps else 0.0
  row["spillover_ratio"] = float(max_other / (t_disp + 1e-8))
  ```
- **Near-Zero Target Safeguard:** An epsilon term $\epsilon = 10^{-6}\text{ m}$ is required to prevent division instability when target displacement is near zero.
- **Regional Aggregation in BICE:** The BICE locality objective evaluates the **maximum regional ratio** rather than an unweighted sum:
  $$\mathcal{L}_{\text{locality}}(\mathbf{s}) = \max_{R \neq R_{\text{target}}} \text{RMSR}_R(\mathbf{s})$$
- **Regional Mask Definitions:** Anny vertex subsets defined by anatomical bounds:
  - `calves`: $Z < -0.40\text{ m}$
  - `thighs`: $-0.40\text{ m} \le Z < -0.05\text{ m}$
  - `hips`: $-0.05\text{ m} \le Z < 0.08\text{ m}$
  - `waist_abdomen`: $0.08\text{ m} \le Z < 0.22\text{ m}$
  - `torso_chest`: $0.22\text{ m} \le Z < 0.40\text{ m}$
  - `shoulders`: $0.40\text{ m} \le Z < 0.50\text{ m}$, $|X| > 0.12\text{ m}$
  - `arms`: $|X| > 0.20\text{ m}$, $Z < 0.40\text{ m}$
  - `head_neck`: $Z \ge 0.50\text{ m}$
- **Parameter Bounds as Provisional Engineering Bounds:**
  - Sweeps at $[-1.0, -0.5, 0.0, +0.5, +1.0]$ in Phase 0 confirmed that extreme values ($+1.0$) for `l-upperleg-fat-incr` produced excessive RMSR ($4.04$), and `stomach-pregnant-incr` produced $1.53$.
  - Boundaries such as Thigh `[-0.50, +0.50]`, Abdomen `[-0.50, +0.70]`, and Shoulder `[-0.75, +0.75]` are **PROVISIONAL ENGINEERING BOUNDS**, not mathematically proven continuous intervals. They will be validated during Phase 3 property tests.

---

## 3. Explicit Technical Boundaries

1. **Model-Derived Estimates vs. Validated Human Truth:**
   - Any measurement extracted from Anny mesh geometry is a **geometric model estimate**.
   - It must never be represented as an externally validated human dimension until Phase 8 volunteer trials.
2. **Provenance, Validation, Lifecycle & Assessment Separation:**
   - Acquisition method (`user_reported`, `tape_measured`, `geometry_extracted`, `model_estimated`), validation state (`unvalidated`, `internally_consistent`, `externally_validated`, `disputed`), lifecycle status (`active`, `superseded`, `draft`, `purged`), and assessment state (`eligible`, `provisional`, `unassessed`, `rejected`) are four orthogonal classifications.
3. **Strict Exclusion of Mass & BMI from Sizing:**
   - Model-derived mass and BMI must never enter garment sizing or personal health claims.
4. **Latency SLAs as Benchmark Targets:**
   - The verified $20.82\text{ ms}$ CPU benchmark is a warm single-mesh forward pass, not an end-to-end API SLA.
   - End-to-end pipeline latency ($<50\text{ ms}$) and API roundtrip SLA ($<150\text{ ms}$ p95) are engineering targets to be benchmarked in Phase 6 load tests.
