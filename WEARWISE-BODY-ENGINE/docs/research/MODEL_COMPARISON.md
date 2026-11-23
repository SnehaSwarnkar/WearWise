# Body Model Comparative Analysis & Selection Scorecard (Reconciled)

**Task:** WearWise Phase 0 Avatar Foundation Comparison  
**Evaluator:** Antigravity (Implementation Executor)  
**Technical Decision Owner:** ChatGPT  
**Decision Status:** NAVER Anny v0.6.2 Selected as Primary Avatar Foundation  
**Evaluation Date:** 2026-11-23  

---

## 1. Model Selection Scorecard

According to Section 7 of the WearWise Master Project Brief, scoring applies to candidates that pass the mandatory legal/licensing gate:

| Evaluation Criterion | Weight | Candidate A: NAVER Anny (v0.6.2) | Candidate B: OxiHuman (v0.0.1 / unreleased) | Winning Candidate & Empirical Evidence |
|---|---|---|---|---|
| **Commercial Licensing Gate** | **MANDATORY GATE** | **PASS** (Apache-2.0 + CC0-1.0; all 34 deps permissive) | **NON-SELECTED / RESTRICTED** (Crates.io v0.0.1 declares BUSL-1.1; repo 404; legal status unresolved) | **Anny passes cleanly.** |
| **1. Anthropometric Usefulness & Validation Potential** | 30% | **8.5 / 10**<br>Direct $Z$-scale verified in meters ($100\times$ to $cm$); native height and waist; calibrated custom 2D slices yield chest ($111.1\text{ cm}$), waist ($67.9\text{ cm}$ vs native $67.1\text{ cm}$), hips ($88.4\text{ cm}$), shoulders ($36.8\text{ cm}$ biacromial, $39.2\text{ cm}$ deltoid); $100\%$ deterministic across runs. | **4.0 / 10**<br>Supports only 4 tape measures (bust, underbust, waist, hips); optimizer residuals reflect synthetic self-consistency on its own mesh, not human tape accuracy; no shoulder breadth. | **Anny (+4.5):** Superior anthropometric extraction, verifiable stature scaling, and landmark definitions. |
| **2. Independent Regional Control Quality** | 20% | **9.0 / 10**<br>254 local morph targets; independent deltoid shoulders (L/R), belly protrusion (`stomach-pregnant-incr`), independent forearms (L/R), thighs, and calves. | **2.0 / 10**<br>Severe gaps: 0 shoulder controls, 0 arm controls, 0 abdomen controls, 0 thigh controls, 0 calf controls. Only 8 macro girth targets. | **Anny (+7.0):** Anny supports true regional customization; OxiHuman is strictly a global silhouette scaler. |
| **3. Mesh & Topology Quality for Neutral Mannequin** | 15% | **9.0 / 10**<br>13,718 vertices, 27,420 faces; clean neutral A-pose; watertight manifold; realistic proportional human mannequin appearance; seamless Three.js rendering. | **7.5 / 10**<br>21,833 vertices (MakeHuman standard adult mesh); good visual quality, but lacks neutral A-pose limb clearance without skeletal rigging. | **Anny (+1.5):** Clean topology optimized for differential deformers. |
| **4. Runtime, Memory & Interactive Performance** | 15% | **9.5 / 10**<br>CPU inference latency: **$20.82\text{ ms}$** (mean); GPU: **$74.45\text{ ms}$**; peak VRAM: **$113.4\text{ MB}$** ($2.7\%$ of 4 GB card); RAM: $\sim 334\text{ MB}$; 100 runs stable with 0 crashes. | **8.0 / 10**<br>Pure Rust/WASM is lightweight in browser ($\sim 15\text{ ms}$ claim), but server-side execution is moot due to repo removal and license restrictions. | **Anny (+1.5):** $20\text{ ms}$ CPU inference enables real-time interactive previews at ₹0 server cost. |
| **5. Operational Maturity & Dependency Stability** | 10% | **8.5 / 10**<br>Published on PyPI by NAVER LABS Europe; clean PyTorch 2.0+ integration; native topology isolates from SMPL; stable binary wheels. | **1.0 / 10**<br>Repository returns 404; crates.io prior releases yanked; transitional release 0.0.1; high operational volatility. | **Anny (+7.5):** Anny is maintained and stable; OxiHuman is inaccessible. |
| **6. GLB & Browser Integration Quality** | 10% | **9.0 / 10**<br>GLB export takes **$3.15\text{ ms}$**; file size **$482.8\text{ KB}$**; passes pygltflib and trimesh validation; ready for Three.js viewer. | **7.0 / 10**<br>Supports GLB export via oxihuman-export, but lacks server pipeline and requires WASM integration. | **Anny (+2.0):** Ultra-fast $3\text{ ms}$ export and sub-500 KB GLB files. |
| **Weighted Total Technical Score** | **100%** | **8.93 / 10.0** | **5.05 / 10.0** (Non-selected) | **ANNY WINS OVERWHELMINGLY.** |

---

## 2. Qualitative Architectural Trade-Offs

### Candidate A: NAVER Anny (Selected Foundation)
- **Strengths:**
  1. **Rich Regional Parametric Space:** 254 local change blendshapes enable fine-grained adjustments across every required WearWise zone (shoulders, chest, abdomen, waist, arms, hips, thighs, calves).
  2. **Exceptional CPU Performance:** $20.8\text{ ms}$ single-body inference on AMD Ryzen 7 6800H means the backend does **not** require costly cloud GPU instances. It runs on low-cost CPU instances or locally at ₹0 cost.
  3. **Low Memory Footprint:** Consumes only $113.4\text{ MB}$ VRAM when run on GPU, leaving $>97\%$ of the RTX 3050's 4 GB frame buffer free.
  4. **Commercial Open Source:** Fully Apache-2.0 with CC0 MakeHuman assets; zero proprietary licensing fees or cloud dependencies.
- **Identified Limitations & Mitigations:**
  1. Built-in `Anthropometry` module is minimal (height, waist, BMI); WearWise maintains its own calibrated geometric slicing module for chest, hips, and limbs.
  2. High-value parameter spillover (e.g. thigh fat) will be constrained via the BICE optimizer to $[-0.5, +0.5]$.

### Candidate B: OxiHuman (Retained as Non-Selected Alternative)
- **Strengths:**
  1. Rust/WASM architecture designed for pure client-side execution in the browser.
- **Defects that Preclude Selection:**
  1. Shipped core pack contains only 38 morph targets, completely lacking independent controls for shoulders, arms, abdomen, thighs, and calves.
  2. Relicensed under BUSL-1.1 on November 17, 2026; prior releases yanked; GitHub repository returns 404.

---

## 3. Formal Recommendation to Technical Decision Owner

**NAVER Anny (Native Topology, v0.6.2) is confirmed as the primary avatar foundation for WearWise.**

This decision is backed by:
1. **Unambiguous Legal Clearance:** Apache-2.0 code and CC0-1.0 assets with permissive transitive dependencies.
2. **Product Requirement Alignment:** Only candidate providing independent shoulder, arm, belly, and leg controls.
3. **Hardware Feasibility:** Validated $20.8\text{ ms}$ CPU inference and $113.4\text{ MB}$ GPU VRAM footprint on local target hardware.
