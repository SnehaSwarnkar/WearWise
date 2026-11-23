# Risks, Limitations & Future Experiment Roadmap

**Document:** WearWise Phase 0 Risk Register & Limitations  
**Status:** Pre-Phase 1 Architectural Handoff  
**Date:** 2026-11-23  

---

## 1. Verified Limitations of Selected Model (NAVER Anny v0.6.2)

1. **Native Anthropometry Module is Incomplete for Apparel:**
   - **Limitation:** Anny's native `anny.Anthropometry` class returns only stature (`height`), `waist_circumference`, enclosed `volume`, `mass`, and `bmi`. It does not extract chest/bust circumference, shoulder breadth, hip circumference, or limb circumferences.
   - **Impact on WearWise:** WearWise cannot rely exclusively on Anny's built-in anthropometry.
   - **Mitigation:** WearWise must maintain its own geometric slicing and landmark-extraction engine (demonstrated successfully in Experiment C and scheduled for formalization in Phase 4).

2. **Waist Slicing vs. Natural Indentation & Arm Isolation:**
   - **Limitation:** A naive horizontal slice across the torso at waist height ($Z \approx 0.13\text{ m}$) can capture resting forearm and wrist vertices if the user's arms are down, resulting in an artificial $+7.80\text{ cm}$ overestimation if not filtered. Furthermore, the true natural waist line has a $1.74\text{ cm}$ vertical tilt along the torso surface rather than a strictly planar cross-section.
   - **Impact on WearWise:** Cross-sectional circumference extraction must isolate the central torso region ($|X| \le 0.20\text{ m}$) before computing the 2D perimeter.
   - **Mitigation:** Implement strict bounding boxes separating torso vertices from limbs during slicing, and compare planar convex hull perimeters against 3D geodesic surface chains.

3. **Skeletal LBS Settling on Stature:**
   - **Limitation:** Posing the mesh with identity bone matrices introduces an $0.87\text{ cm}$ ($0.55\%$) height delta between the unposed template rest vertices ($156.83\text{ cm}$) and the skinned bounding box ($155.97\text{ cm}$).
   - **Impact on WearWise:** Inconsistent height reporting if bounding box and template stature are mixed.
   - **Mitigation:** WearWise establishes canonical landmark-to-landmark distance (crown vertex to plantar foot vertex) as the canonical stature metric.

4. **Native Buoyancy-Derived BMI & Mass are NOT Personal Truth:**
   - **Limitation:** Anny calculates body mass and BMI by assuming a constant human tissue density ($\rho \approx 980\text{ kg/m}^3$) across all body shapes.
   - **Impact on WearWise:** Presenting model-derived BMI or weight as verified facts would misinform users and violate WearWise's core principle of honest fit intelligence.
   - **Mitigation:** Tag native mass/BMI strictly as `model_estimated` and exclude them from garment ease calculations. Weight entered by the user must be stored as `user_reported`.

5. **Regional Spillover at High Parameter Values:**
   - **Limitation:** Certain local changes (e.g. `l-upperleg-fat-incr`, spillover ratio $4.04$; `stomach-pregnant-incr`, spillover ratio $1.53$) cause geometric expansion in adjacent pelvic regions when pushed to extreme values ($1.0$).
   - **Impact on WearWise:** Extreme slider settings can distort neighboring body zones.
   - **Mitigation:** The BICE optimizer (Phase 3) must constrain user-facing slider ranges to the $[-0.75, +0.75]$ safe zone and apply a locality penalty term $\lambda_l$ to penalize unwanted regional spillover.

6. **Raw Morph Targets Must NOT be Exposed in Consumer UI:**
   - **Limitation:** Anny's 254 local morph targets are low-level mathematical vertex deltas (e.g. `l-upperarm-scale-horiz-incr`, `measure-waist-circ-incr`). Directly exposing these to consumer shoppers would create a confusing, overwhelming, and un-ergonomic user experience.
   - **Impact on WearWise:** Potential UI fragmentation and user frustration.
   - **Mitigation:** WearWise must enforce an abstraction layer in Phase 2 and 3. Consumers will interact with intuitive, high-level semantic sliders (e.g. "Arm Fit", "Shoulder Width", "Waist Definition") that the BICE solver maps to bounded Anny morph parameter vectors.

7. **Arm Angles in Reference Pose:**
   - **Limitation:** Anny's neutral reference pose features arms slightly abducted downward ($\sim 30^\circ$ angle). Horizontal slicing across the upper torso slices through the arms at an angle.
   - **Mitigation:** To extract true bicep and wrist circumferences, slices must be taken perpendicular to the local humerus/radius bone coordinate vectors rather than along the global $Z$-plane.

8. **Windows Smart App Control & Warp DLL:**
   - **Limitation:** Windows 11 Smart App Control blocks `warp.dll` when attempting GPU Warp skinning (`WinError 4551`).
   - **Mitigation:** Initializing Anny with `skinning_method="lbs"` uses PyTorch's native dense linear blend skinning, which runs smoothly on both CPU and CUDA without triggering Windows security blocks, while delivering $20.8\text{ ms}$ inference.

---

## 2. Outstanding Blockers & Resolved Questions

| Item | Prior Status | Phase 0 Resolution |
|---|---|---|
| OxiHuman Evaluation Status | Disputed in Revision 1 | **Retained as Non-Selected Alternative:** Relicensed on crates.io to `BUSL-1.1` on 2026-11-17; prior releases yanked; GitHub 404. Decisively rejected due to absence of regional controls for shoulders, arms, abdomen, thighs, and calves. |
| PyTorch CUDA 13.0 on RTX 3050 | Provisional assumption | **Empirically Proven:** PyTorch 2.14.1+cu130 installs and runs real tensor compute on CUDA:0. |
| RTX 3050 4 GB VRAM Headroom | High risk assumption | **Empirically Disproven as Risk:** Anny consumes only $113.4\text{ MB}$ VRAM ($2.7\%$ of 4 GB). VRAM is more than ample. |
| Anny Coordinate Units | Unknown | **Empirically Proven:** Native coordinate units are **METERS** ($100.0\times$ factor to $cm$). |
| Neutral Mannequin Topology | Unknown | **Empirically Proven:** 13,718 vertices, 27,420 faces; watertight; neutral appearance; exports to $482.8\text{ KB}$ GLB. |
| Waist Discrepancy ($7.80\text{ cm}$) | Inconsistent | **Empirically Reconciled:** Isolated torso slice yields $67.90\text{ cm}$, matching native $67.11\text{ cm}$ within $0.79\text{ cm}$ ($1.18\%$). |

---

## 3. What Remains Unproven (Pre-Phase 1 Boundaries)

1. **External Human Ground-Truth Accuracy:**
   - Feasibility experiments demonstrated that Anny is internally consistent, controllable, and geometrically extractable.
   - However, **we have not yet proven how closely Anny's default shapes match real human bodies across diverse populations (including Indian demographics)**.
   - This cannot be proven mathematically with synthetic meshes; it requires the volunteer tape-measure validation study scheduled in **Phase 8**.

2. **Garment Ease Calibration:**
   - Phase 0 established that body dimensions can be extracted in centimeters.
   - The exact numerical ease bands (e.g. $+4\text{ cm}$ ease for slim T-shirt chest vs $+10\text{ cm}$ for relaxed) remain to be calibrated against actual physical T-shirt fit trials in Phase 5.

---

## 4. Recommended Next Experiment (Phase 1 Gate)

The immediate next task for ChatGPT and the project owner is to **freeze Phase 0** and proceed to **Phase 1: Architecture, Schemas & API Contract Design**:
1. Formalize the `BodyProfile` and `BodyMeasurement` Pydantic schemas using the proven meter-to-centimeter scale ($100\times$) and verified measurement dictionary.
2. Design the FastAPI modular monolith service boundaries (`avatar_engine/`, `bice/`, `fit_engine/`).
3. Maintain Anny in an isolated adapter (`avatar_engine/adapters/anny_adapter.py`) so the rest of the application remains model-agnostic.
