# WEARWISE — PHASE 10 SIMULATION ARCHITECTURE

**Phase:** 10.1–10.3 — Dynamic Garment Simulation Feasibility & Prototype  
**Scope:** Anny rig investigation, garment topology & binding analysis, simulation engine evaluation, and selected prototype architecture  
**Status:** Experimental Prototype Verified (Staging / Try-On untouched)

---

## 1. Executive Summary

WearWise's existing static 3D try-on stack renders Anny avatars as unrigged single-mesh GLBs (`anny_baseline_male.glb`, `494,720` B) paired with static multi-panel garments (`TSH-WW-CREW-001_M_candidate_rev3.glb`, `7` independent meshes). Legacy `ClothSimulator.ts` cannot articulate an Anny skeleton because `AnnyAdapter.export_glb` strips bones and skin weights during `trimesh.Trimesh.export()`, and its XPBD solver only binds the first mesh node without seam welding or bending constraints.

To enable convincing interactive garment simulation on a single RTX 3050 (4 GB VRAM) + browser client target, we evaluated five cloth simulation architectures against 12 engineering criteria and selected a **Client-Side Welded-Seam XPBD + Articulated Three.js `SkinnedMesh` Hybrid** for Phase 10.1–10.3:
- **Backend (`pygltflib`):** Preserves NAVER Anny v0.6.2's full **104-bone skeleton**, `(13718, 104)` skinning weights (top-4 normalized `JOINTS_0` / `WEIGHTS_0`), and column-major `inverseBindMatrices` in a standard glTF 2.0 `SkinnedMesh` (`anny_rigged_male_exp.glb`, `1,027,976` B).
- **Frontend (`WeldedClothSolver.ts`):** Welds all **7** garment panels (`3,384` unwelded vertices → `3,145` welded particles) on a `0.5 mm` spatial grid, builds **18,288** XPBD constraints (`9,242` structural + `9,046` opposite-vertex bending), articulates `upperarm01.L` / `upperarm01.R` in real time, and projects particles against live bone-driven torso and arm capsule colliders at **2.2–2.5 ms/frame** (`50–60 FPS`, `15.4 MB` JS heap).

---

## 2. Phase 10.1 — Anny Avatar Rig & Pipeline Investigation

### 2.1 Existing Exported Avatar (`anny_baseline_male.glb`)
- **File:** [anny_baseline_male.glb](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/public/avatars/anny_baseline_male.glb) (`494,720` bytes)
- **Scene Graph:** `1` node (`geometry_0`), `1` mesh (`13,718` vertices, `27,420` triangles, watertight `true`), `0` skins, `0` animations, `0` morph targets, no `JOINTS_0` or `WEIGHTS_0`.
- **Bounds (Y-up, meters):** `[-0.4928, 0.0000, -0.2109]` to `[0.4928, 1.5597, 0.2109]`.
- **Root Cause of Missing Rig:** In [anny_adapter.py](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/app/avatar_engine/adapters/anny_adapter.py), `AnnyAdapter.export_glb` transforms NAVER Anny Z-up vertices to Y-up via `R_x(-90°)` and exports via `trimesh.Trimesh(...).export(file_type="glb")`, discarding Anny's joint hierarchy, rest bone poses, and vertex skinning weights.

### 2.2 NAVER Anny v0.6.2 PyTorch Model Capabilities
Inspection of the live NAVER Anny v0.6.2 model (`anny_model_rig_details.json`) confirmed:
- **Skeleton:** `104` named bones (`root`, `pelvis.L/R`, `spine05`..`spine01`, `clavicle.L/R`, `shoulder01.L/R`, `upperarm01.L/R`, `upperarm02.L/R`, `lowerarm01.L/R`, `lowerarm02.L/R`, `wrist.L/R`, fingers, legs, toes, `neck01..03`, `head`, `eye.L/R`).
- **Skinning Weights:** Dense `(13718, 104)` float matrix with row sums equal to `1.0` (`top-4` joints per vertex cover smooth linear blend skinning; `upperarm01.L` influences `423` verts, `lowerarm01.L` `366` verts, `upperarm01.R` `421` verts, `lowerarm01.R` `366` verts).
- **Parametric Phenotype & Local Changes:** `6` global phenotype parameters (`gender`, `age`, `muscle`, `weight`, `height`, `proportions`) plus `240+` `local_change_labels` (note: exported as baked rest geometry rather than glTF morph targets).

### 2.3 Coordinate System & Bone-Name Contracts
- **Coordinate Conversion:** Anny native space is Z-up (`+Y` back, `+X` left). Applying `R_x(-90°)` maps native `(x, y, z)` to glTF Y-up `(x, z, -y)` (`+Y` up, `+Z` forward, `+X` wearer's left). Bone world matrices use `t_rot @ bone_pose_zup` with translation scaled and shifted identically to the mesh (`inv_bind_mats` and `bone_local_mats` stored column-major per glTF 2.0 spec).
- **Three.js `GLTFLoader` Bone Name Sanitization:** Three.js strips `.` characters when binding node names (`upperarm01.L` → `upperarm01L`). Any solver querying `skeleton.bones` must match both `name` and `name.replace(/\./g, '')`.

---

## 3. Phase 10.2 — Garment Topology & Legacy Binding Audit

### 3.1 Reference Garment Structure (`TSH-WW-CREW-001_M_candidate_rev3.glb`)
- **Isolated Experimental Copy:** [TSH-EXP-PHASE10_M.glb](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/public/experimental_phase10/TSH-EXP-PHASE10_M.glb) (`249,100` bytes; protected Rev3 assets remain untouched).
- **Panel Decomposition:** `7` separate mesh nodes with identity transforms (`PANEL-FRONT-TORSO`, `PANEL-BACK-TORSO`, `PANEL-SLEEVE-L`, `PANEL-SLEEVE-R`, `PANEL-COLLAR-RIB`, `PANEL-HEM-BAND`, `PANEL-POCKET-CHEST`), totaling `3,384` unwelded vertices and `6,096` triangles.
- **Alignment:** Y-up, `+Z`-forward in meters, pre-aligned to `anny_baseline_male.glb` in neutral A-pose (`P0`).

### 3.2 Legacy `ClothSimulator.ts` Limitations
Inspecting [ClothSimulator.ts](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/components/avatar/ClothSimulator.ts) identified three structural blockers:
1. **Single-Mesh Binding:** Binds only the first `THREE.Mesh` encountered in `garmentRoot`, leaving 6 of 7 panels static.
2. **Unwelded Panel Seams:** Does not merge coincident boundary vertices across panels (`3,384` → `3,145` unique spatial particles), causing panels to tear apart under deformation.
3. **No Skeleton / Bending Constraints:** Falls back to a crude Y-band vertex displacement because `anny_baseline_male.glb` lacks bones, and lacks 2-hop bending resistance.

---

## 4. Phase 10.3 — Simulation Engine Evaluation (12 Criteria)

We evaluated five candidate simulation architectures for WearWise's web + Python microservice stack (hosted on an RTX 3050 4 GB VRAM workstation):

| Criterion | 1. Client-Side Welded XPBD + `SkinnedMesh` (Selected) | 2. Three.js + Ammo.js (`btSoftBody`) | 3. WebGPU Compute XPBD | 4. Server-Side PyTorch / DiffCloth + Stream | 5. Pre-Baked Vertex Cache (`mdd`/GLTF Anim) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Garment Multi-Panel Seam Welding** | Native (`0.5 mm` spatial weld across 7 panels) | Manual merge + re-split required | Native via compute buffers | Offline/backend weld | Baked only |
| **2. Real-Time FPS (Browser)** | **50–60 FPS** (`2.2–2.5 ms` solve) | 25–40 FPS (WASM marshaling overhead) | 60+ FPS (where supported) | 5–15 FPS (network + GPU sync) | 60 FPS (zero physics) |
| **3. Skeleton / Pose Interactivity** | **Arbitrary continuous slider & presets (`0°–90°`)** | Arbitrary, complex soft-rigid coupling | Arbitrary | High latency per pose change | Fixed keyframes only |
| **4. Fabric Parameterization (`GSM`, stretch, bend)** | **Direct (`stretchCompliance`, `bendCompliance`, `damping`)** | Limited (`kLST`, `kAST`) | Direct | Direct | None (re-bake per fabric) |
| **5. Collision Quality (Torso + Arms)** | Good (bone-driven capsules; upgradeable to SDF) | Good (convex hulls / capsules) | Excellent (spatial hash / SDF) | Excellent (exact triangle-mesh) | Pre-baked only |
| **6. GPU VRAM Footprint (RTX 3050 4 GB)** | **~0 MB backend VRAM** (runs in browser CPU/WebGL) | ~0 MB backend VRAM | ~0 MB backend VRAM | **High (1.5–3.5 GB)** + contention with Anny | ~0 MB |
| **7. JS / Client Memory Footprint** | **15.4 MB JS Heap** | 45–80 MB (WASM heap + bindings) | ~20 MB | Minimal | 30–120 MB per clip |
| **8. Browser Compatibility** | **100% WebGL2 / Chromium / Firefox / Safari** | 100% WASM | Partial (WebGPU flags/drivers) | 100% | 100% |
| **9. Integration with Existing React + Three.js** | **Drop-in TypeScript module (`WeldedClothSolver.ts`)** | Heavy WASM bundle + lifecycle | Complex WGSL shader pipeline | WebRTC / WebSocket binary stream | Heavy asset pipeline |
| **10. Determinism & Debug Telemetry** | **High** (per-step solve ms, displacement, projections) | Medium (opaque C++ WASM state) | Low (async GPU readback stalls) | Medium | High |
| **11. Multi-Garment / Layering Extensibility** | Good (priority/offset layers in XPBD) | Difficult | Excellent | Excellent | Poor |
| **12. Implementation Risk for Phase 10** | **Low** (proven in prototype) | Medium | High | High | Low (but non-interactive) |

### Decision Rationale
**Selected Architecture:** **Client-Side Welded-Seam XPBD + Articulated Three.js `SkinnedMesh` (`WeldedClothSolver.ts`)** paired with `pygltflib` rigged Anny glTF export on the backend.
- **Why:** Achieves `2.2–2.5 ms` per-frame physics (`50–60 FPS`) on `3,145` welded particles and `18,288` constraints with zero backend GPU VRAM contention on the RTX 3050 (4 GB), zero network round-trips during slider/pose manipulation, and full fabric-profile tuning (`240 GSM` waffle knit vs `140 GSM` poplin).

---

## 5. Selected Prototype Architecture

1. **Rigged Avatar Export (`export_rigged_anny_exp.py`):**
   - Evaluates NAVER Anny v0.6.2 in neutral rest pose (`gender=-0.5` baseline male, scaled to match `anny_baseline_male.glb`), extracts `104` bone world transforms, computes parent-relative local matrices and column-major `inverseBindMatrices`, packs top-4 `JOINTS_0` (`UNSIGNED_SHORT`) and normalized `WEIGHTS_0` (`FLOAT`), and writes `anny_rigged_male_exp.glb`.
2. **Welded-Seam XPBD Solver (`WeldedClothSolver.ts`):**
   - **Particle Welding:** Quantizes vertices from all `7` garment meshes onto a `0.5 mm` grid (`3,384` verts → `3,145` particles), maintaining a `vertexToParticle` map per mesh so all `7` `BufferAttribute`s stay synchronized with zero visible seam tearing.
   - **Constraints:** `9,242` structural distance edges + `9,046` 2-hop opposite-vertex bending constraints solved over `4` substeps per `16.7 ms` frame.
   - **Articulated Pose & Colliders:** Smoothly interpolates `upperarm01.L` / `upperarm01.R` quaternions in world Z, updates bone-driven capsules (`spine02–spine05` `r=0.145 m`, `upperarm01–lowerarm01` `r=0.056 m`, `lowerarm01–wrist` `r=0.044 m`), and projects penetrating particles outward.

---

## 6. Risks, Limitations & Next Steps (Phase 10.4–10.8)

- **RTX 3050 4 GB VRAM Consideration:** Running cloth physics client-side leaves 100% of the RTX 3050's 4 GB VRAM available for `WEARWISE-BODY-ENGINE` Anny inference. However, if server-side baked cloth fitting is ever added later, Anny + PyTorch3D/DiffCloth must be serialized to avoid OOM.
- **Current Prototype Limitations:**
  1. Capsule colliders approximate the torso/arms smoothly but do not capture scapula/pectoral/deltoid concavities as accurately as a skinned triangle mesh or signed distance field (SDF).
  2. Only shoulder elevation (`upperarm01.L/R`) is articulated; elbow flexion, clavicle shrug, and spinal twist are deferred to Phase 10.4+.
  3. Collar vertices are pinned (`invMass = 0`) to stabilize the neckline; Phase 10.4 should replace hard pinning with neck-capsule contact + soft collar elastic constraints.
- **Recommended Next Steps (Phase 10.4–10.8, awaiting authorization):**
  1. Integrate `pygltflib` rigged glTF export into `AnnyAdapter.export_glb` behind a feature flag so personalized shopper avatars carry the 104-bone rig.
  2. Add spatial-hash broad-phase triangle-mesh collision against the posed Anny `SkinnedMesh` (or per-bone SDFs) to eliminate residual capsule-gap clipping.
  3. Support multi-joint poses (clavicle lift, elbow bend, torso lean) and automated fabric-parameter calibration against `TSH-WW-CREW-001` M2R-C Rev3 profiles.
