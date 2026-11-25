# WEARWISE — PHASE 10 PROTOTYPE REPORT

**Phase:** 10.1–10.3 — Dynamic Garment Simulation Feasibility & Prototype  
**Experimental Route:** `/experimental-phase10` ([Phase10SimPage.tsx](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/experimental_phase10/Phase10SimPage.tsx))  
**Solver Module:** [WeldedClothSolver.ts](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/experimental_phase10/WeldedClothSolver.ts)  
**Verification Script:** [verify_phase10_poses.py](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/verify_phase10_poses.py)

---

## 1. Implemented Prototype Scope

An isolated experimental simulation sandbox was built at `/experimental-phase10` without modifying protected `TSH-WW-CREW-001` Rev3 S/M/L assets, `frontend/public/garments/`, production MongoDB databases, or the shopper `/try-on` route:

1. **Experimental Rigged Anny Asset ([anny_rigged_male_exp.glb](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/public/experimental_phase10/anny_rigged_male_exp.glb)):**
   - Generated via [export_rigged_anny_exp.py](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/export_rigged_anny_exp.py) (`1,027,976` bytes).
   - Contains `1` `SkinnedMesh` (`13,718` vertices, `27,420` triangles), `104` skeleton bones, top-4 `JOINTS_0` / normalized `WEIGHTS_0`, and column-major `inverseBindMatrices`.
2. **Experimental Garment Copy ([TSH-EXP-PHASE10_M.glb](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/public/experimental_phase10/TSH-EXP-PHASE10_M.glb)):**
   - Isolated copy of `TSH-WW-CREW-001` M Rev3 (`249,100` bytes, `7` mesh panels, `3,384` unwelded vertices, `6,096` triangles).
3. **Interactive Controls & Telemetry (`Phase10SimPage.tsx`):**
   - Articulated pose presets (`P0: 0°`, `P1: 30°`, `P2: 45°`, `P3: 90°`) + continuous elevation slider (`0°–90°`).
   - Fabric profile toggle (`Cotton Waffle Knit 240 GSM` vs `Structured Poplin 140 GSM`) and wireframe toggle.
   - Live telemetry HUD reporting rig bone count, particle/constraint counts, solve time, FPS, max cloth displacement, capsule collision projections/step, and JS heap usage.

---

## 2. Measured Pose Verification Results (`P0`–`P3`)

Captured via headless Chromium Playwright against `vite preview` (`http://127.0.0.1:4173/experimental-phase10`) in [phase10_pose_results.json](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_pose_results.json):

| Pose | Arm Elevation | Rig Status | Solve Time | FPS (Current / Avg / Min) | Max Cloth Displacement | Capsule Projections / Step | JS Heap | Visual Observation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **P0** | `0°` (Neutral A-Pose) | `SkinnedMesh=true \| Bones=104` | `2.3 ms` | `60 / 54 / 30` | `6.96 cm` | `491` | `15.4 MB` | Clean neutral drape; collar, chest pocket, sleeves, and hem aligned. |
| **P1** | `30°` Elevation | `SkinnedMesh=true \| Bones=104` | `2.2 ms` | `60 / 54 / 30` | `15.64 cm` | `484` | `15.4 MB` | Both Anny arms elevate 30°; welded sleeves follow smoothly with natural underarm creasing. |
| **P2** | `45°` Elevation | `SkinnedMesh=true \| Bones=104` | `2.2 ms` | `60 / 54 / 30` | `22.23 cm` | `468` | `15.4 MB` | Horizontal T-pose articulation; shoulder/armhole seams remain welded with no tearing. |
| **P3** | `90°` Elevation | `SkinnedMesh=true \| Bones=104` | `2.5 ms` | `60 / 50 / 30` | `39.32 cm` | `488` | `15.4 MB` | Overhead V-pose; arms and sleeves elevate symmetrically with deltoid/underarm folding and anchored collar/pocket. |

**Mesh & Constraint Counts (All Poses):**
- **Avatar Vertices:** `13,718`
- **Garment Vertices → Welded Particles:** `3,384` → `3,145`
- **XPBD Constraints:** `18,288` (`9,242` structural + `9,046` bending)
- **Timestep:** `16.7 ms` (`4` substeps)

### Screenshots
- `P0 (0°)`: [phase10_pose_P0.png](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_pose_P0.png)
- `P1 (30°)`: [phase10_pose_P1.png](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_pose_P1.png)
- `P2 (45°)`: [phase10_pose_P2.png](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_pose_P2.png)
- `P3 (90°)`: [phase10_pose_P3.png](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_pose_P3.png)

---

## 3. Build, Test & Preservation Verification

- **Frontend Unit Tests (`npm test`):** `4` test files, `13` tests passed (`13/13`), exit code `0`.
- **Frontend Production Build (`npm run build`):** `tsc --noEmit && vite build` succeeded in `547 ms`, exit code `0`.
- **Protected Rev3 Asset Checksums (`protected_rev3_intact: true` in `phase10_pose_results.json`):**
  - `S`: `8f9bd0c79c54d4f40e3354f729c5f236634acec3a06d33a1f0ec771b51e41690` (intact)
  - `M`: `9b6212ff218ba6231000cdca1716f808fd501df4e843353655ec7ce4d7389769` (intact)
  - `L`: `4bc1a0cbcb0cccbe3b4bd5646b614bc881a06d5db06ec44b0034a577e8101387` (intact)

---

## 4. Known Defects & Observations

1. **Expected Standalone Preview Network Errors:** Running `vite preview` standalone without backend servers on ports `8000` / `8001` logged 3 `ERR_CONNECTION_REFUSED` console/network errors from global `Header`/cart/profile polling (`/api/cart/*`, `/health`, `/api/v1/profiles`). The `/experimental-phase10` simulation itself has zero backend dependencies and rendered cleanly.
2. **Capsule Collider Approximation:** Using 5 body/arm capsules (`spine02–spine05`, `upperarm01–lowerarm01`, `lowerarm01–wrist`) yields ~`468–491` projections/step with minor fabric-into-deltoid compression at `90°` elevation (`P3`). Accurate anatomical contact requires triangle-mesh or SDF collision in Phase 10.4+.
3. **Pinned Collar Ring:** Collar vertices are currently pinned (`invMass = 0`) to prevent neckline slide during extreme arm elevation.

---

## 5. Gate Verdict Table (P10.1–P10.8)

| Gate | Description | Verdict | Evidence |
| :--- | :--- | :--- | :--- |
| **P10.1** | Anny rig & `AnnyAdapter.export_glb` root-cause investigation completed | **PASS** | `rig_and_garment_inspection.json`, `anny_model_rig_details.json`, `anny_adapter.py` |
| **P10.2** | Garment topology (`7` panels, `3,384` verts) & legacy `ClothSimulator.ts` gaps documented | **PASS** | `rig_and_garment_inspection.json`, `ClothSimulator.ts` |
| **P10.3** | Rigged 104-bone experimental Anny GLB exported & validated (`SkinnedMesh`, `JOINTS_0`, `WEIGHTS_0`) | **PASS** | `export_rigged_anny_exp.py`, `anny_rigged_male_exp.glb`, Playwright telemetry (`Rig: SkinnedMesh=true \| Bones=104`) |
| **P10.4** | Multi-panel seam welding (`3,384` → `3,145` particles) + structural/bending XPBD (`18,288` constraints) | **PASS** | `WeldedClothSolver.ts`, `phase10_pose_results.json` |
| **P10.5** | Articulated pose tests `P0 (0°) / P1 (30°) / P2 (45°) / P3 (90°)` verified visually & via telemetry | **PASS** | `phase10_pose_P0.png`..`P3.png`, `phase10_pose_results.json` |
| **P10.6** | Real-time performance target (`< 16.7 ms` solve, `>= 30 FPS`, bounded JS heap) | **PASS** | `2.2–2.5 ms` solve time, `50–54` avg FPS (`30` min, `60` current), `15.4 MB` JS heap |
| **P10.7** | Preservation of protected Rev3 S/M/L assets, `public/garments/`, DBs, and `/try-on` | **PASS** | `protected_rev3_intact: true` (all 3 SHA-256 checksums verified) |
| **P10.8** | Architecture & Prototype deliverables (`WEARWISE_PHASE10_SIMULATION_ARCHITECTURE.md`, `WEARWISE_PHASE10_PROTOTYPE_REPORT.md`) | **PASS** | Both files written and verified in repository root |
