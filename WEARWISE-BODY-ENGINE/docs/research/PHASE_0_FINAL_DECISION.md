# WearWise Phase 0 Final Technical Decision & Gate Sign-Off

**Project:** WearWise AI Fashion & Honest Fit Platform  
**Document:** Phase 0 Final Technical Decision Record (TDR-001)  
**Date of Decision:** 2026-11-23  
**Implementation Executor:** Antigravity (Google DeepMind Team)  
**Technical Decision Owner:** ChatGPT  
**Decision Status:** **FORMALLY APPROVED & SIGNED OFF — PHASE 0 CLOSED**  

---

## 1. Context and Objective

Phase 0 of the WearWise project was instituted as an empirical technical gate to determine whether a user can generate a realistic, proportionally accurate, measurement-grounded 3D body representation without a photograph, camera, or body scan, within strict local hardware constraints:
- **Target Machine:** Windows 11 Home x64, AMD Ryzen 7 6800H CPU, 16 GB RAM, NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM).
- **Commercial & Infrastructure Mandate:** ₹0 initial infrastructure budget; mandatory commercial licensing eligibility (permissive open-source only).
- **Core Product Requirement:** Anatomically responsive neutral mannequin supporting independent regional editing across 8 required zones: shoulders, torso/chest, abdomen, waist, upper/lower arms, hips, thighs, and calves, with automated geometric measurement extraction and binary GLB export for React Three Fiber rendering.

Two candidates were evaluated in depth:
1. **NAVER Anny (v0.6.2, Native Topology)**
2. **OxiHuman (crates.io package & core asset pack)**

---

## 2. Final Technical Decision

### PRIMARY SELECTION: NAVER Anny v0.6.2 (Native Topology)

**NAVER Anny v0.6.2 with Native Topology is formally selected as the primary 3D avatar engine for the WearWise platform.**

#### Summary of Empirical Justifications:
1. **Commercial Licensing Cleared:**
   - **Code License:** Apache License 2.0 (Permissive; commercial SaaS use and modification permitted).
   - **Asset License:** CC0-1.0 Universal Public Domain Dedication (Derived from MakeHuman community assets).
   - **SMPL Isolation:** Restricted SMPL/SMPL-X/SMPL-H meshes and dependencies (`smplx`, `chumpy`) were strictly excluded.
   - **Transitive Dependencies:** All 34 installed dependencies are permissively licensed (Apache-2.0, BSD-3-Clause, MIT). Zero AGPL/GPL copyleft contamination.
2. **Superior Morphological Controllability:**
   - Exposes **254 local morph targets** in its native configuration.
   - Empirically verified coverage across **all 8 required WearWise regions**:
     - *Shoulders:* `measure-shoulder-dist-incr`, `l-upperarm-shoulder-muscle-incr`, `r-upperarm-shoulder-muscle-incr`.
     - *Torso / Chest:* `breast-point-incr`, `breast-dist-incr`, `breast-volume-vert-up`, pectoral definition via `muscle`.
     - *Abdomen:* `stomach-pregnant-incr` (belly wall protrusion), `stomach-navel-out`.
     - *Waist:* `hip-waist-up` (vertical waist position), `measure-waist-circ-incr`, global girth scaling.
     - *Arms:* Pure localized unilateral controls (`l-upperarm-scale-horiz-incr`, `l-lowerarm-scale-depth-incr`, `l-lowerarm-fat-incr`) with **0.00 spillover**.
     - *Hips:* `hip-trans-out`, `buttocks-volume-incr`.
     - *Thighs:* `l-upperleg-fat-incr`, `r-upperleg-fat-incr`.
     - *Calves:* `measure-calf-circ-incr`, `measure-lowerleg-height-incr`.
3. **Hardware Performance & Budget Compliance (₹0 Mandate):**
   - **CPU Inference:** **$20.82\text{ ms}$** mean warm latency on AMD Ryzen 7 6800H ($+334\text{ MB}$ RAM). Zero CUDA kernel launch overhead makes CPU inference $3.5\times$ faster than single-mesh GPU execution, enabling smooth 50 FPS real-time interactive previews on commodity CPU worker threads.
   - **GPU Headroom:** Consumes only **$113.4\text{ MB}$ VRAM** ($2.7\%$ of 4 GB RTX 3050), completely dispelling VRAM bottleneck concerns.
4. **Clean Web-Ready Mesh Generation:**
   - Watertight topology: **13,718 vertices and 27,420 triangular faces**.
   - Direct binary GLB export: **$3.15\text{ ms}$** generation time; **$482.8\text{ KB}$** file size.
   - Supports both male (`gender=1.0`) and female (`gender=0.0`) anatomical baselines in a standardized neutral A-pose.

---

## 3. Rejection and Status of Non-Selected Alternative

### CANDIDATE: OxiHuman (crates.io / cool-japan)

**Status: Retained as a non-selected alternative.**

#### Technical and Licensing Grounds for Rejection:
1. **Severe Product & Capability Gaps:**
   - The shipped core pack (`oxihuman-core-v1.ohpk`) provides only **38 morph targets** (30 macro-details and 8 girth pairs for bust, underbust, waist, and hip).
   - **Zero** independent controls exist for shoulders (no biacromial or deltoid adjustments), upper arms (no bicep/tricep scaling), lower arms (no forearm or wrist controls), abdomen protrusion (no forward belly wall displacement), thighs (no upper leg girth), or calves (no lower leg circumference).
   - OxiHuman cannot fulfill WearWise's core requirement of personalized regional fit adjustments for apparel.
2. **Licensing & Distribution Instability:**
   - On November 17, 2026, crates.io package `oxihuman` v0.0.1 was published under `license = "BUSL-1.1"` (Business Source License 1.1), restricting commercial production use until 2030.
   - All prior Apache-2.0 versions (`0.1.0`, `0.2.1`) were yanked from crates.io.
   - The official GitHub repository (`https://github.com/cool-japan/oxihuman`) returns HTTP 404 (removed, renamed, or made private).
   - While historical Apache-2.0 commits remain theoretically available and mesh assets trace to MakeHuman CC0-1.0, commercial adoption carries unacceptable operational and legal risks for WearWise.

---

## 4. Key Anthropometric Reconciliations

1. **Waist Circumference Discrepancy Resolved:**
   - *Issue:* In initial tests, Anny's native waist measurement returned $67.11\text{ cm}$, while a custom geometric slice returned $74.91\text{ cm}$ (a $7.80\text{ cm}$ difference).
   - *Investigation:* Anny defines waist circumference as a 3D closed polygonal chain across 46 anatomical vertices (`BASE_MESH_WAIST_VERTICES`) at the natural waist indentation ($Z \approx 0.1334\text{ m}$, $60.83\%$ stature), which has an anatomical vertical curve ($\Delta Z = 1.74\text{ cm}$). The initial naive slice sliced at $66\%$ stature without limb filtering, inadvertently capturing resting forearm/wrist vertices in the 2D convex hull.
   - *Resolution:* Filtering out lateral limb vertices ($|X| \le 0.20\text{ m}$) at natural waist height ($Z = 0.1334\text{ m}$) yields a planar convex hull perimeter of **$67.90\text{ cm}$**, matching native within **$0.79\text{ cm}$ ($1.18\%$)**. The remaining $0.79\text{ cm}$ represents the difference between a planar horizontal perimeter and the true 3D anatomical surface curvature.
2. **Stature (Height) Discrepancy Resolved:**
   - Native unposed template vertices measure $156.83\text{ cm}$ ($Z = -0.8206\text{ m}$ to $+0.7477\text{ m}$).
   - Posed mesh under identity linear blend skinning has a bounding box height of $155.97\text{ cm}$ ($Z = -0.8391\text{ m}$ to $+0.7206\text{ m}$).
   - The $0.87\text{ cm}$ ($0.55\%$) difference is standard skeletal LBS settling across the ankle, spine, and neck joints.
3. **Coordinate Scale:**
   - Coordinate units are strictly **METERS** ($1.0\text{ m} = 100.0\text{ cm}$).
4. **Ground-Truth Boundary:**
   - Extracted measurements are **model-derived geometric estimates**. They are mathematically reproducible on the 3D mesh surface, but external accuracy against diverse real human bodies (including varied Indian demographics) remains unproven and will be formally validated in Phase 8.
   - Volume-derived body mass ($43.49\text{ kg}$) and BMI ($17.68$) are based on an assumed uniform density ($\rho = 980\text{ kg/m}^3$) and must be strictly excluded from garment sizing or personal health claims.

---

## 5. UI and Architectural Abstraction Directive

1. **No Raw Morph Targets in Consumer UI:**
   - Anny's 254 local morph targets are low-level mathematical vertex displacement vectors.
   - Consumer shoppers must never be presented with raw internal parameter names or unbounded float inputs.
   - The WearWise frontend will expose high-level, human-friendly sliders (e.g. "Shoulder Width", "Waist Definition", "Chest Fullness", "Arm Muscularity").
2. **BICE Abstraction & Calibration Layer:**
   - The Body Intelligence & Calibration Engine (BICE), to be designed in Phase 2 and implemented in Phase 3, will act as the mediation layer.
   - BICE will convert high-level user sliders and tape measurements into bounded Anny parameter vectors, enforcing parameter safety bounds ($[-0.75, +0.75]$) and applying locality penalties ($\lambda_l$) to prevent unwanted regional spillover.
3. **Adapter Isolation:**
   - All Anny interactions must be encapsulated within `avatar_engine/adapters/anny_adapter.py`.
   - The rest of the WearWise application (schemas, fit engine, frontend API) will remain completely agnostic to the underlying 3D avatar engine.

---

## 6. Phase 0 Acceptance Criteria Verification Matrix

| # | Acceptance Criterion | Target / Standard | Empirically Verified Value | Status |
|---|---|---|---|---|
| AC-1 | Target Environment Verified | Real OS, CPU, RAM, GPU | Win 11, Ryzen 7 6800H, 16 GB RAM, RTX 3050 (4 GB) | **PASS** |
| AC-2 | PyTorch Isolated Install | No global pollution | `.venv-anny` isolated, PyTorch 2.14.1+cu130 | **PASS** |
| AC-3 | Native Anny Inference | Generate male & female | Male (1.56 m), Female (1.70 m), 13,718 vertices | **PASS** |
| AC-4 | Usable GLB Export | Export, valid, web-sized | Binary GLB in $3.15\text{ ms}$, $482.8\text{ KB}$ | **PASS** |
| AC-5 | Morph Parameter Analysis | 20+ params, 8 regions | 20 params swept, 254 cataloged, spillover quantified | **PASS** |
| AC-6 | Anthropometry Grounding | Coordinate scale & slices | Scale = meters ($100\times$), waist & height reconciled | **PASS** |
| AC-7 | OxiHuman Capability Audit | 38 targets, crates.io audit | 38 targets evaluated, 6 region gaps, BUSL-1.1 verified | **PASS** |
| AC-8 | Latency & Memory Benchmarks | CPU & GPU benchmarks | CPU: $20.82\text{ ms}$, RAM: $+334\text{ MB}$, VRAM: $113.4\text{ MB}$ | **PASS** |
| AC-9 | Transitive Licensing Audit | Code, assets, dependencies | Anny: Apache-2.0, Assets: CC0-1.0, 34/34 deps permissive | **PASS** |
| AC-10 | Evidence Package Delivered | Code, JSON, GLBs, docs | 6 JSON outputs, 7 OBJs, 25 GLBs, 6/6 tests passing | **PASS** |

---

## 7. Phase 0 Gate Sign-Off & Transition to Phase 1

### Sign-Off Statement
**Phase 0: Body Model Feasibility, Licensing and Hardware Validation is formally COMPLETED and CLOSED.**

All technical, licensing, and hardware gates have been cleared. In accordance with the Project Owner's instructions:
- No complete backend (`WEARWISE-CORE`) has been constructed.
- No database migrations or microservices were created.
- No existing frontend files were modified.

### Phase 1 Hand-Off Directive:
The project may now transition to **Phase 1: Architecture, Schemas & API Contract Design**:
1. Formalize the core Pydantic data schemas: `BodyProfile`, `BodyMeasurement`, `GarmentSpecs`, and `FitRecommendation`.
2. Define the modular monolith directory structure and service interfaces for `avatar_engine`, `bice`, and `fit_engine`.
3. Establish OpenAPI/Swagger specifications for avatar generation, slider manipulation, and GLB delivery.
4. Maintain strict backward compatibility with the existing React + Vite / Three.js frontend.

*Signed on behalf of the implementation team,*  
**Antigravity (Google DeepMind Team)**  
*Execution Executor for WearWise Phase 0*
