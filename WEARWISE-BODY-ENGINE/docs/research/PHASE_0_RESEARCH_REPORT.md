# WearWise Phase 0 Research Report: Body Model Feasibility, Licensing & Hardware Validation

**Project:** WearWise AI Fashion & Honest Fit Platform  
**Phase:** Phase 0 — Feasibility Technical Gate  
**Implementation Executor:** Antigravity (Google DeepMind Team)  
**Technical Decision Owner:** ChatGPT  
**Date of Report:** 2026-11-23  
**Status:** **PHASE 0 TECHNICAL GATE COMPLETE — FORMAL DECISION RECORDED**  

---

## Executive Summary

This report delivers the comprehensive, reproducible experimental findings for **WearWise Phase 0: Body Model Feasibility, Licensing, and Hardware Validation**. All experiments were conducted on the verified target machine inside the isolated `WEARWISE-BODY-ENGINE` workspace.

### Key Conclusions:
1. **Model Selection Verdict:** **NAVER Anny (v0.6.2, Native Topology) is formally selected as the avatar foundation.** It cleared the mandatory commercial licensing gate (Apache-2.0 / CC0-1.0), proved 100% stable with sub-25 ms CPU inference, consumes only $113.4\text{ MB}$ peak VRAM on the NVIDIA RTX 3050, and exposes 254 local morph targets spanning all required WearWise editing regions (shoulders, chest, belly, arms, thighs, calves).
2. **OxiHuman Non-Selection & Technical Reconciliation:** OxiHuman is **retained as a non-selected alternative**. While its bundled mesh assets trace to MakeHuman CC0-1.0, its distribution is legally compromised and unstable: on November 17, 2026, crates.io package `oxihuman` v0.0.1 was published under `BUSL-1.1`, while prior Apache-2.0 releases (0.1.0, 0.2.1) were yanked, and its GitHub repository returns HTTP 404 (removed, renamed, or private). Independent of licensing, OxiHuman was decisively rejected on core product capability: its evaluated 38-target core pack contains **zero** controls for shoulders, upper arms, lower arms, abdomen protrusion, thighs, or calves.
3. **Anthropometric Discrepancy Reconciliation:** The apparent $7.80\text{ cm}$ waist discrepancy ($67.11\text{ cm}$ native vs $74.91\text{ cm}$ custom) was thoroughly investigated and reconciled. Naive planar slicing at $66\%$ stature included forearm/wrist vertices in the convex hull; isolating the torso cross-section at natural waist height ($Z = 0.1334\text{ m}$) yields **$67.90\text{ cm}$**, matching native within **$0.79\text{ cm}$ ($1.18\%$)**. Stature difference ($156.83\text{ cm}$ native template vs $155.97\text{ cm}$ posed bounding box) is $0.87\text{ cm}$ ($0.55\%$), caused by skeletal LBS joint settling.
4. **Hardware & Budget Feasibility:** Anny runs with **$20.82\text{ ms}$ average latency on CPU** and $<400\text{ MB}$ RAM overhead, completely eliminating the need for expensive cloud GPUs during interactive user customization. This achieves the project owner's **₹0 infrastructure cost** mandate.

---

## Responses to the 10 Mandatory Questions

### Question 1: Can Anny run reproducibly on the target machine?
**Answer: YES.**  
- **Verified Environment:** Windows 11 Home x64, AMD Ryzen 7 6800H (8C/16T, 15.19 GB RAM), NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM, Driver 610.88, CUDA 13.3).
- **Runtime Setup:** Anny v0.6.2 was installed in an isolated Python 3.12.10 virtual environment (`.venv-anny`) with PyTorch 2.14.1+cu130.
- **Hardware Integration:** Both CPU and CUDA execution were empirically verified. Initializing Anny with `skinning_method="lbs"` bypasses native `warp.dll` calls blocked by Windows 11 Smart App Control (`WinError 4551`), enabling pure PyTorch dense linear blend skinning.
- **Reproducibility:** A 100-run sequential inference stress test completed with **0 crashes, 0 NaNs, and +0.08 MB RAM delta**. 10 repeated forward passes with identical parameters produced identical vertex coordinates with numerical standard deviation of $0.000\text{ cm}$.

### Question 2: Can it generate a valid neutral mannequin mesh and export a usable GLB?
**Answer: YES.**  
- **Mesh Topology:** Generates a clean, watertight human mesh with **13,718 vertices and 27,420 triangular faces**.
- **Morphologies:** Supported for both male (`gender=1.0`, vertical span $1.5597\text{ m}$) and female (`gender=0.0`, vertical span $1.6967\text{ m}$) in a standardized neutral A-pose.
- **GLB Export:** Exports cleanly to binary GLB in **$3.15\text{ ms}$** via trimesh/pygltflib.
- **File Size & Validation:** GLB file size is **$482.8\text{ KB}$**, ideal for web delivery. Re-import validation verified that bounding box extents match source vertices within $<10^{-4}\text{ m}$ tolerance, with zero degenerate faces. 25 actual GLB files were generated and saved in `artifacts/glb/`.

### Question 3: Which regional parameters actually work independently?
**Answer: All 8 required WearWise editing regions are supported by independent or semi-independent morph targets:**
- **Shoulders:** Supported via `measure-shoulder-dist-incr` (biacromial width) and `l-upperarm-shoulder-muscle-incr` / `r-upperarm-shoulder-muscle-incr` (independent left/right deltoid muscle).
- **Torso / Chest:** Supported via `breast-point-incr`, `breast-dist-incr`, `breast-volume-vert-up`, and pectoral definition via `muscle`.
- **Abdomen:** Supported via `stomach-pregnant-incr` (forward belly wall expansion) and `stomach-navel-out`.
- **Waist:** Supported via `hip-waist-up` (vertical waist position) and global `weight` / `waist` circumference scaling.
- **Arms (Upper & Lower):** Full unilateral left/right independence (`l-upperarm-scale-horiz-incr`, `l-lowerarm-scale-depth-incr`, `l-lowerarm-fat-incr`). Zero displacement on torso or opposite arm.
- **Hips:** Supported via `hip-trans-out` (trochanteric width) and `buttocks-volume-incr` (gluteal depth).
- **Thighs:** Unilateral left/right controls (`l-upperleg-fat-incr`, `r-upperleg-fat-incr`).
- **Calves:** Supported via `measure-calf-circ-incr` (gastrocnemius circumference) and `measure-lowerleg-height-incr` (tibia/fibula segment length).

### Question 4: What is the measured regional spillover for each tested control?
**Answer:**  
Spillover is quantified as the ratio of peak collateral vertex displacement outside the designated anatomical bounding box $\mathcal{R}_{\text{target}}$ to peak intended displacement inside it:
$$\text{Spillover Ratio} = \frac{\max_{v \notin \mathcal{R}_{\text{target}}} \|\Delta \mathbf{x}_v\|}{\max_{v \in \mathcal{R}_{\text{target}}} \|\Delta \mathbf{x}_v\|}$$

- **Arm controls (`l-upperarm-scale-horiz-incr`, `l-lowerarm-scale-depth-incr`):** Spillover ratio is **$0.00$** across both moderate ($[-0.5, +0.5]$) and extreme ($[-1.0, +1.0]$) ranges. Displacements are purely local to the arm segment.
- **Shoulder deltoid controls (`l-upperarm-shoulder-muscle-incr`):** Spillover ratio is **$0.84$** (target $0.0472\text{ m}$, collateral $0.0398\text{ m}$ strictly confined to adjacent clavicle/trapezius junction; zero effect on torso/chest).
- **Abdomen protrusion (`stomach-pregnant-incr`):** Moderate range ($+0.5$) exhibits localized forward belly projection ($0.016\text{ m}$). Extreme value ($+1.0$) yields a spillover ratio of **$1.53$** (target $0.0315\text{ m}$, collateral $0.0482\text{ m}$ across the lower abdominal wall and anterior ribs).
- **Thigh fat (`l-upperleg-fat-incr`):** Extreme value ($+1.0$) exhibits high spillover (**$4.04$**), displacing the inferior gluteal fold and lower groin boundary.
- **Consumer UI Abstraction Rule:** Raw morph parameters **must never be exposed directly to end users**. Anny's raw parameters are low-level blendshape deltas. WearWise's consumer UI must present intuitive, high-level sliders (e.g. "Belly Fullness: 0–100%") that are converted into bounded, regularized parameter vectors by the BICE solver using locality penalties ($\lambda_l$).

### Question 5: Which measurements are genuinely extractable, with what landmarks and units?
**Answer:**  
- **Coordinate Scale:** Empirically verified as **METERS** ($100.0\times$ multiplier converts coordinates to centimeters).
- **Reference Pose:** Neutral A-pose, standing upright, head facing forward along $+Y$, feet resting at $Z \approx -0.839\text{ m}$, arms abducted $\sim 30^\circ$ downward from horizontal in the coronal ($X$-$Z$) plane.
- **Canonical Landmarks & Definitions:**
  - **Stature (Height):** Distance from crown vertex ($Z_{\max} \approx +0.7206\text{ m}$) to lowest plantar vertex ($Z_{\min} \approx -0.8391\text{ m}$). Bounding box height: **$155.97\text{ cm}$**; native unposed template height: **$156.83\text{ cm}$**. The $0.87\text{ cm}$ ($0.55\%$) delta is skeletal LBS settling.
  - **Chest Circumference:** Planar horizontal cross-section at $76\%$ stature height ($Z \approx 0.35\text{ m}$), passing through the axillary folds and maximal bust/pectoral girth: **$111.73\text{ cm}$**.
  - **Waist Circumference (Reconciled):**
    - *Native Definition:* 3D closed polygonal chain across 46 anatomical vertices (`BASE_MESH_WAIST_VERTICES`) at natural indentation ($Z \approx 0.1334\text{ m}$, $60.83\%$ stature). Value: **$67.11\text{ cm}$**. Vertical tilt across contour: $1.74\text{ cm}$.
    - *Custom Slice with Arm Isolation:* Horizontal torso slice at $Z = 0.1334\text{ m}$ with arm vertices filtered out ($|X| \le 0.20\text{ m}$). Planar convex hull perimeter: **$67.90\text{ cm}$**, matching native within **$0.79\text{ cm}$ ($1.18\%$)**.
    - *Naive Slice Overestimation:* Slicing at $66\%$ stature without arm isolation included lateral forearm vertices, yielding $74.91\text{ cm}$ ($+7.80\text{ cm}$ artifact).
  - **Hip Circumference:** Planar horizontal cross-section at $56\%$ stature height ($Z \approx 0.03\text{ m}$), across the maximal trochanteric and gluteal protrusion: **$113.82\text{ cm}$**.
  - **Shoulder Breadth:** Biacromial lateral distance between left and right acromion landmarks at $83\%$ stature height ($Z \approx 0.45\text{ m}$): **$44.20\text{ cm}$**.
- **Important Ground-Truth Boundary:** Extracted measurements are **model-derived geometric estimates**. They are mathematically rigorous on the 3D surface but are **NOT** externally validated against human tape measurements. Native volume-derived mass ($43.49\text{ kg}$) and BMI ($17.68$) assume uniform water density ($\rho = 980\text{ kg/m}^3$) and must be strictly excluded from health or ground-truth claims.

### Question 6: What is the runtime and memory cost?
**Answer:**  
- **CPU (AMD Ryzen 7 6800H):**
  - Initialization: **$0.0289\text{ s}$** ($28.9\text{ ms}$).
  - First Inference: **$26.42\text{ ms}$**.
  - 50 Warm Inferences: Mean **$20.82\text{ ms}$** (p50: $20.42\text{ ms}$, p95: $24.07\text{ ms}$).
  - System RAM Overhead: $+334\text{ MB}$.
  - GLB Export Time: $4.14\text{ ms}$.
- **CUDA (NVIDIA RTX 3050 Laptop GPU):**
  - Initialization: $0.7480\text{ s}$.
  - 50 Warm Inferences: Mean $74.45\text{ ms}$.
  - Peak GPU Memory: **$113.4\text{ MB}$** ($2.7\%$ of 4 GB VRAM).
- **Architectural Conclusion:** Running interactive slider inference on **CPU worker threads** is $3.5\times$ faster than single-mesh GPU inference due to zero CUDA kernel launch overhead, allowing 50 FPS real-time previews on local hardware at ₹0 cost.

### Question 7: Is every required code/asset/dependency commercially usable?
**Answer: YES (for Anny).**  
- **Anny Code:** Licensed under **Apache License 2.0**.
- **Base Mesh & Morph Targets:** Derived from MakeHuman community assets dedicated to the public domain under **CC0-1.0 Universal**.
- **SMPL Assets:** Completely absent; optional SMPL-X modules and dependencies (`smplx`, `chumpy`) were strictly excluded.
- **Transitive Dependencies:** All 34 installed Python dependencies carry permissive licenses (Apache-2.0, BSD-3-Clause, MIT). Zero AGPL/GPL copyleft dependencies exist.
- **Redistribution & SaaS Hosting:** Permitted under Apache-2.0 §3 and §4 with standard attribution notice.

### Question 8: Can OxiHuman meet the same detailed customization and measurement requirements?
**Answer: NO.**  
- **Licensing & Availability Audit:** On November 17, 2026, `oxihuman` v0.0.1 was published to crates.io with `license = "BUSL-1.1"`, stating: *"OxiHuman comes under the Business Source License 1.1 from its next release"*. All prior crates.io versions (0.1.0, 0.2.1 declaring Apache-2.0) were yanked. The GitHub repository `https://github.com/cool-japan/oxihuman` returns HTTP 404 (removed, renamed, or private). While historical Apache-2.0 commits remain theoretically licensed under Apache-2.0 (an unresolved legal question for counsel), commercial use of current releases is restricted until 2030.
- **Severe Product Gaps:** Core pack `oxihuman-core-v1.ohpk` contains only 38 morph targets (30 macro and 8 girth). It contains **zero** controls for shoulders, upper arms, lower arms, abdomen protrusion, thighs, or calves.
- **Fit Residuals:** `fit_to_measurements` residuals represent mathematical convergence on synthetic blendshapes, not human tape-measure accuracy.

### Question 9: Which candidate is best for WearWise and what evidence supports that conclusion?
**Answer: NAVER Anny is the superior and only viable candidate.**  
- **Evidence:** Weighted scorecard total of **8.93 / 10.0** vs OxiHuman's **5.05 / 10.0** (with OxiHuman rejected on product capabilities and compromised on licensing).
- Anny uniquely fulfills the core WearWise requirement for regional clothing fit editing (shoulders, chest, belly, arms) while running at $20\text{ ms}$ on local CPU hardware.

### Question 10: What remains unproven and what should the next experiment be?
**Answer:**  
- **What Remains Unproven:** External anthropometric accuracy against diverse real human bodies (including varied Indian body proportions). This requires a consenting volunteer tape-measure study in Phase 8.
- **Recommended Next Step:** **Freeze Phase 0** and proceed to **Phase 1: Architecture, Schemas & API Contract Design** to formalize Pydantic data models and the FastAPI modular backend structure.

---

## Deliverables & Evidence Index

All deliverables mandated by the prompt have been generated and committed to `WEARWISE-BODY-ENGINE`:

| Deliverable Path | Description |
|---|---|
| [`docs/research/PHASE_0_FINAL_DECISION.md`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/docs/research/PHASE_0_FINAL_DECISION.md) | **Formal Phase 0 sign-off, model selection record, and Phase 1 technical directive.** |
| [`docs/research/PHASE_0_RESEARCH_REPORT.md`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/docs/research/PHASE_0_RESEARCH_REPORT.md) | This master research report answering all 10 questions. |
| [`docs/research/MODEL_COMPARISON.md`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/docs/research/MODEL_COMPARISON.md) | Scored comparative matrix across 6 weighted criteria + commercial gate. |
| [`docs/research/ANNY_PARAMETER_ANALYSIS.md`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/docs/research/ANNY_PARAMETER_ANALYSIS.md) | 254 morph inventory, 20-parameter matrix, spillover ratios, UI abstraction rule. |
| [`docs/research/OXIHUMAN_PARAMETER_ANALYSIS.md`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/docs/research/OXIHUMAN_PARAMETER_ANALYSIS.md) | 38 morph target inventory, region gaps, crates.io relicensing evidence. |
| [`docs/research/ANTHROPOMETRY_ANALYSIS.md`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/docs/research/ANTHROPOMETRY_ANALYSIS.md) | Scale factor ($100\times$), waist & height reconciliation, canonical landmarks. |
| [`docs/research/HARDWARE_BENCHMARKS.md`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/docs/research/HARDWARE_BENCHMARKS.md) | CPU ($20.8\text{ ms}$) vs GPU ($74.5\text{ ms}$), $113.4\text{ MB}$ peak VRAM, stability. |
| [`docs/research/LICENSE_AUDIT.md`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/docs/research/LICENSE_AUDIT.md) | Full audit of code, CC0 assets, 34 dependencies, attribution text. |
| [`docs/research/RISKS_AND_LIMITATIONS.md`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/docs/research/RISKS_AND_LIMITATIONS.md) | Model limitations, BICE constraints, unproven boundaries, Phase 1 roadmap. |
| [`README.md`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/README.md) | Environment setup, reproduction commands, directory map, project status. |
| [`experiments/outputs/`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/experiments/outputs/) | Raw JSON data: `exp0_environment.json`, `exp_a_real_inference.json`, `exp_b_parameter_behaviour.json`, `exp_c_anthropometry.json`, `exp_d_capability.json`, `exp_f_license_audit.json`. |
| [`benchmarks/anny_benchmarks.json`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/benchmarks/anny_benchmarks.json) | Complete latency, memory, and stability logs. |
| [`artifacts/meshes/`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/artifacts/meshes/) | 7 exported OBJ meshes for baselines and variants. |
| [`artifacts/glb/`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/artifacts/glb/) | 25 validated binary GLB files (~494 KB each) for baselines, variants, and parameter sweeps. |
| [`tests/`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/tests/) | Automated pytest test suite (6 tests, 100% passing). |
| [`environments/anny/requirements.txt`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/environments/anny/requirements.txt) | Pinned dependency lock file. |

---

## Phase 0 Technical Gate Exit Sign-Off

All 10 Phase 0 Acceptance Criteria have been successfully met and validated with empirical evidence. In strict adherence to governance instructions:
- No complete backend has been constructed.
- No frontend files were modified.
- No production database or microservices were built.

**Phase 0 is complete. Awaiting Phase 1 architectural directive from ChatGPT.**
