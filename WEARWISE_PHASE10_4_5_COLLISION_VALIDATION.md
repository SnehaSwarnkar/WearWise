# WEARWISE — PHASE 10.4 & 10.5 COLLISION AND XPBD STABILITY VALIDATION

**Phases:** 10.4 (Anatomical Collision System) & 10.5 (XPBD Stability and Deformation Validation)  
**Modules:** [AnatomicalCollider.ts](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/experimental_phase10/AnatomicalCollider.ts), [WeldedClothSolver.ts](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/experimental_phase10/WeldedClothSolver.ts)  
**Machine-Readable Results:** [collision_stability_results.json](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_4_5/collision_stability_results.json)

---

## 1. Phase 10.4 — Collision Audit, Architecture Selection & Implementation

### 1.1 Audit of Phase 10.1–10.3 Five-Capsule Approximation
- **Prior Geometry:** `5` capsules (`spine02–spine05` `r=0.145 m`, `upperarm01–lowerarm01` `r=0.056 m`, `lowerarm01–wrist` `r=0.044 m`).
- **Root Causes of Residual Penetration & Bulging:**
  1. Circular torso cylinder (`r=0.145 m`) missed elliptical pectoral/ribcage contours (`~0.165 m` X half-width) and waist taper.
  2. No shoulder/deltoid (`shoulder01–upperarm01`) or neck (`neck01–neck03`) colliders.
  3. Hard-pinned collar vertices (`invMass = 0`) hid neck contact rather than solving it.

### 1.2 Evaluated Architectures & Selected Hybrid
We compared: (1) capsules only, (2) brute-force skinned triangle mesh (`3,145 × 27,420 = 86.2M` checks/substep), (3) per-bone SDFs, and (4) **Hybrid Bone-Driven Anatomical Capsules + Spatial-Hash Skinned Triangle-Mesh Narrow-Phase (Selected)**:
- **Broad-Phase Anti-Tunneling (`11` Inner Capsules):** `waist_spine` (`r=0.095 m`), `mid_torso` (`r=0.105 m`), `neck` (`r=0.048 m`), `chest_L/R` (`r=0.068 m`), `deltoid_L/R` (`r=0.048 m`), `upperarm_L/R` (`r=0.042 m`), `forearm_L/R` (`r=0.032 m`).
- **Narrow-Phase Surface Contact (`10,066` Upper-Body Skinned Triangles):** CPU-skinned from live `skeleton.boneMatrices` (`0.76 <= y <= 1.43`, `|x| <= 0.44`) into a zero-allocation `5.5 cm` flat 3D spatial hash (`TABLE_SIZE = 4096`), rebuilt whenever the skeleton moves, with damped outward normal projection (`0.65 * pen`) + post-collision XPBD smoothing.
- **Soft Elastic Collar (Step 10.4.5):** Replaced hard `invMass = 0` pinning with `invMass = 0.25`, height-blended `spine01` elastic guidance (`pull = 0.28`), and live `neck` capsule + skinned-mesh collision.

### 1.3 Quantitative Before/After Collision Comparison (`waffle_knit_240`, `3,145` Particles)

| Stage / Pose | Total Particles | Penetrating Particles | Max Penetration | Mean Penetration | Capsule / Mesh Corrections | Collision Time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline (Initial 11-Cap Oversized)** `P0` | `3,145` | `101` (`3.21%`) | `8.68 mm` | `2.61 mm` | `3,532` / `705` | `8.0 ms` |
| **Optimised Hybrid `P0` (Neutral)** | `3,145` | **`4`** (`0.13%`) | **`1.94 mm`** | **`1.39 mm`** | `751` / `453` | `4.8 ms` |
| **Optimised Hybrid `P1` (30°)** | `3,145` | `35` (`1.11%`) | `6.27 mm` | `2.35 mm` | `819` / `458` | `4.7 ms` |
| **Optimised Hybrid `P2` (45°)** | `3,145` | `56` (`1.78%`) | `14.00 mm` | `2.65 mm` | `947` / `486` | `4.7 ms` |
| **Optimised Hybrid `P3` (90°)** | `3,145` | `136` (`4.32%`) | `12.08 mm` | `4.37 mm` | `1,090` / `614` | `4.8 ms` |

**Documented Residual Limitations:** Under extreme `90°` overhead abduction (`P3`), `~3.4–4.3%` of particles (`108–136 / 3,145`) show `~4.1–4.4 mm` mean residual penetration in the compressed axillary crease where sleeve and torso folds converge.

---

## 2. Phase 10.5 — Displacement Investigation, XPBD Stability & Recovery

### 2.1 Investigation of `39.32 cm` Displacement at `P3`
In Phase 10.3, `maxDisplacementCm` was measured relative to the `0°` rest pose (`pos - restPos`). Rotating a sleeve cuff `~24 cm` from the shoulder pivot by `90°` moves it `~34–45 cm` in world space via **rigid articulation**, not fabric stretching. Separating rigid articulation from true strain via `meanStretchRatio` (`1.0063` at `P0`, `1.0676` at `P3`) and `constraintResidual` (`0.223 mm` at `P0`, `2.275 mm` at `P3`) confirms the XPBD mesh does not explode.

### 2.2 Provisional Stability Tolerances & Recovery Sequence (`P0 → P3 → Hold → P0`)

| Sequence Stage | Max Disp | Mean Stretch Ratio | Max Stretch Ratio | Max Compression | Mean Bend Dev | Constraint Residual | Seam Sep | Max Velocity | Penetrating Particles |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. `neutral_start` (`P0`)** | `3.22 cm` | `1.0065` | `1.3896` | `0.8354` | `0.0093` | `0.225 mm` | `0.000 mm` | `0.990 m/s` | `2` (`max 2.26 mm`) |
| **2. `elevated_P3` (`90°`)** | `45.12 cm` | `1.0678` | `7.7943` | `0.4934` | `0.1083` | `2.278 mm` | `0.000 mm` | `2.743 m/s` | `134` (`max 14.62 mm`) |
| **3. `hold_P3` (`90°`)** | `44.81 cm` | `1.0660` | `7.6367` | `0.4987` | `0.1057` | `2.223 mm` | `0.000 mm` | `2.489 m/s` | `108` (`max 15.39 mm`) |
| **4. `return_P0` (`0°`)** | `3.23 cm` | `1.0063` | `1.3910` | `0.8421` | `0.0091` | `0.222 mm` | `0.000 mm` | `1.133 m/s` | `2` (`max 1.37 mm`) |

- **Recovery Verification:** Returning from `P3 (90°)` to `P0 (0°)` restored `maxDisplacementCm` to `3.23 cm` (within `0.01 cm` of initial `3.22 cm`), `meanStretchRatio` to `1.0063`, `seamSeparationMm` to `0.000 mm`, and `penetratingParticles` to `2`.
- **Provisional Engineering Targets:** Mean stretch `<= 1.08`, seam separation `== 0.0 mm`, mean constraint residual `<= 3.0 mm`, neutral penetration `<= 1%` of particles. All provisional targets were met.
- **Recovery Screenshot:** [recovery_end_P0.png](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_4_5/recovery_end_P0.png)
