# WEARWISE — PHASE 10.7 FABRIC CALIBRATION & PERFORMANCE REPORT

**Phase:** 10.7 — Fabric Physics Calibration and Performance Optimisation  
**Module:** [FabricProfiles.ts](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/experimental_phase10/FabricProfiles.ts)  
**Machine-Readable Logs:** [sustained_waffle_knit_240.json](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_7/sustained_waffle_knit_240.json), [sustained_rigid_poplin_140.json](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_7/sustained_rigid_poplin_140.json)

---

## 1. Structured Fabric Parameter Architecture (`provisional_calibrated`)

All parameters below are provisional simulation constants (pending physical Kawabata/KES-F lab testing), not empirical material constants:

| Parameter | Cotton Waffle Knit (`waffle_knit_240`) | Structured Poplin (`rigid_poplin_140`) |
| :--- | :--- | :--- |
| **Areal Density** | `240 GSM` | `140 GSM` |
| **Thickness** | `1.40 mm` | `0.65 mm` |
| **Stretch Compliance** | `4.5e-6` | `5.0e-7` (`9×` stiffer) |
| **Warp / Weft Resistance** | `1.15 / 0.82` (higher weft give) | `1.45 / 1.35` (tighter woven lock) |
| **Shear Compliance** | `9.0e-6` | `1.5e-6` |
| **Bending Compliance** | `5.5e-4` (softer drape) | `4.5e-5` (crisp fold resistance) |
| **Damping / Friction** | `0.955 / 0.42` | `0.935 / 0.28` |
| **Recovery Stiffness / Gravity Scale** | `0.050 / 1.18` | `0.090 / 0.82` |

---

## 2. Controlled Fabric Comparison (`P1`–`P11` Identical Pose Sequences)

| Pose | Knit Mean Stretch | Poplin Mean Stretch | Knit Mean Bend Dev | Poplin Mean Bend Dev | Knit Residual | Poplin Residual | Knit Max Disp | Poplin Max Disp |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **P1 (30°)** | `1.0201` | `1.0168` | `0.0355` | `0.0299` | `0.768 mm` | `0.673 mm` | `16.89 cm` | `16.66 cm` |
| **P2 (45°)** | `1.0350` | `1.0273` | `0.0579` | `0.0458` | `1.223 mm` | `1.021 mm` | `25.47 cm` | `24.83 cm` |
| **P3 (90°)** | `1.0676` | `1.0586` | `0.1083` | `0.0927` | `2.275 mm` | `1.990 mm` | `45.13 cm` | `44.30 cm` |
| **P8 (85°+Elbow)** | `1.0561` | `1.0497` | `0.0932` | `0.0785` | `1.965 mm` | `1.724 mm` | `42.51 cm` | `41.21 cm` |
| **P11 (Combined)** | `1.0313` | `1.0259` | `0.0618` | `0.0484` | `1.310 mm` | `1.084 mm` | `30.00 cm` | `29.08 cm` |

Across every articulated pose, Structured Poplin exhibits measurably lower stretch (`-0.3%` to `-0.9%`), lower bending deviation (`-14%` to `-21%`), and tighter constraint residuals than Cotton Waffle Knit.

---

## 3. Performance Optimisation & 60-Second Sustained Browser Benchmarks

### Optimisations Applied
1. Cropped skinned collision subset to garment-relevant upper-body region (`21,308` → `10,066` tris).
2. Cached CPU skinning + spatial-hash rebuilds when skeleton pose is unchanged.
3. Ran narrow-phase mesh collision on substeps `0` and `3` (capsules on all `4` substeps) and throttled penetration telemetry to every 3rd step.
4. Converted XPBD constraints to flat typed arrays (`Int32Array` / `Float32Array` / `Uint8Array`) for zero-GC stepping.

### Baseline vs Optimised (`60 s` Sustained Headless Chromium Runs)

| Metric | Baseline (Pre-Opt `waffle_knit_240`) | Optimised `waffle_knit_240` (`61.89 s`) | Optimised `rigid_poplin_140` (`62.06 s`) |
| :--- | :--- | :--- | :--- |
| **Average FPS** | `30.0` | **`38.18`** | **`40.0`** |
| **Minimum FPS** | `30` | `30` | `30` |
| **Avg / Max Solve Time** | `13.64 ms / 16.20 ms` | **`7.71 ms / 9.30 ms`** | **`8.15 ms / 9.30 ms`** |
| **Avg Collision Time** | `7.92 ms` | **`5.03 ms`** | **`5.39 ms`** |
| **Mean P95 Frame Time** | `33.0 ms` | `33.0 ms` | `33.0 ms` |
| **JS Heap (Start → End)** | `17.4 MB → 17.4 MB` (`0.0 MB`) | `18.4 MB → 18.4 MB` (`0.0 MB`) | `17.4 MB → 17.4 MB` (`0.0 MB`) |

**Bottleneck & Target Note:** Solve time dropped by `43.5%` (`13.64 ms` → `7.71 ms`) with `0.0 MB` memory growth, `30` min FPS, and `33.0 ms` P95 frame time. Headless Chromium (`38.2–40.0` avg FPS) falls below the `45` avg FPS target due to headless WebGL software/readback overhead; moving XPBD + spatial-hash collision into a dedicated Web Worker (decoupled from Three.js rendering) is recommended for Phase 11 if >50 FPS is required on low-power laptops.
