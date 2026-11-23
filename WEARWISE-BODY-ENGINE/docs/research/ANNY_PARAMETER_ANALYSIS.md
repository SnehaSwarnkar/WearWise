# Anny Parameter Behaviour, Spillover & Controllability Analysis

**Candidate:** NAVER Anny v0.6.2 (Native Topology)  
**Evaluation Mode:** Actual Local GPU Inference (`cuda:0`, NVIDIA RTX 3050 Laptop GPU 4 GB)  
**Experiment Date:** 2026-11-23  
**Status:** 🧪 Actual Experiment Result / ✅ Pinned Code Inspection  

---

## 1. Parameter Architecture & Inventory

NAVER Anny parameterizes human body morphology through two decoupled tiers:

1. **High-Level Phenotype Parameters (6 Parameters, $[0.0, 1.0]$ Continuous):**
   - `gender`: Blends between male and female biological morphology templates.
   - `age`: Multi-age lifespan growth scaling from infancy to old age (WHO statistics calibrated).
   - `height`: Vertical skeletal stature scaling.
   - `weight`: Adiposity and soft-tissue mass expansion.
   - `muscle`: Muscular bulk, definition, and tone.
   - `proportions`: Trunk-to-leg skeletal length ratio.

2. **Fine-Grained Local Morph Targets (254 Targets, $[-1.0, 1.0]$ Continuous):**
   - Anny exposes **254 artist-authored local morph targets** derived from the MakeHuman community and calibrated using scan-free anthropometric priors.
   - Categories include: `head`, `face`, `neck`, `torso`, `breast`, `stomach`, `waist`, `hip`, `buttocks`, `upperarm`, `lowerarm`, `hand`, `upperleg`, `lowerleg`, and `foot`.
   - Both symmetric bilateral controls and independent unilateral ($L / R$) controls exist across limbs and shoulders.

---

## 2. Evaluation Methodology & Spillover Calculation

### A. Controlled Sweep Protocol
To avoid geometry collapse, every parameter was tested across two distinct regimes against a fixed baseline (Male `gender=1.0, age=0.5, height=0.5, weight=0.5, muscle=0.5, proportions=0.5`, identity A-pose):
- **Moderate Range:** $[-0.5, 0.0, +0.5]$ (safe interactive envelope).
- **Extreme Range:** $[-1.0, +1.0]$ (boundary stress test, evaluated only if moderate values pass).

### B. Mathematical Definition of Spillover Ratio
Mesh vertices were segmented into anatomical region masks using verified geometric and landmark boundaries (with $Z$ as the vertical axis). For each tested local parameter:
$$\text{Displacement Vector: } \Delta \mathbf{v}_i = \mathbf{v}_i^{\text{changed}} - \mathbf{v}_i^{\text{baseline}}, \quad d_i = \|\Delta \mathbf{v}_i\|_2$$
$$\text{Mean Target Displacement: } \bar{d}_{\text{target}} = \frac{1}{|R_{\text{target}}|} \sum_{i \in R_{\text{target}}} d_i$$
$$\text{Max Non-Target Displacement: } d_{\text{max, non-target}} = \max_{j \notin R_{\text{target}}} d_j$$
$$\mathbf{\text{Spillover Ratio}} = \frac{d_{\text{max, non-target}}}{\bar{d}_{\text{target}} + \epsilon}$$

- **Ratio $\le 1.0$:** Highly localized; displacement is concentrated primarily within the intended anatomical zone.
- **Ratio $1.0 < r \le 2.0$:** Moderate localized blending; smooth falloff into adjacent transitional junctions (e.g. breast tissue blending into ribcage).
- **Ratio $> 2.0$:** **Insufficiently localized control**; significant collateral deformation outside the target region requiring optimizer constraints.

---

## 3. Systematic Matrix of the 20 Tested Parameters

| Parameter Name | Type | Range | Test Values Swept | WearWise Region | Moderate Max Disp ($m$) | Extreme Max Disp ($m$) | Spillover Ratio (at $0.5$) | Unilateral ($L/R$) Support? | Geometric Validity | Controllability & Localization Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `height` | Phenotype | $[0, 1]$ | $[0, 0.25, 0.75, 1]$ | Global Stature | $0.2482$ | $0.3644$ | Global | Symmetric | Valid | Global vertical expansion along $Z$; maintains realistic proportions across limbs. |
| `weight` | Phenotype | $[0, 1]$ | $[0, 0.25, 0.75, 1]$ | Global Adiposity | $0.0381$ | $0.0530$ | Global | Symmetric | Valid | Radial expansion of torso, belly, and limbs; highest volume concentration at waist. |
| `muscle` | Phenotype | $[0, 1]$ | $[0, 0.25, 0.75, 1]$ | Global Muscle | $0.0374$ | $0.0538$ | Global | Symmetric | Valid | Enhances deltoids, pectorals, bicep peak, and calves without excessive bone scaling. |
| `proportions` | Phenotype | $[0, 1]$ | $[0, 0.25, 0.75, 1]$ | Global Ratio | $0.0452$ | $0.0662$ | Global | Symmetric | Valid | Shifts torso height vs leg length while keeping overall stature constant. |
| `l-upperarm-shoulder-muscle-incr` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Left Shoulder | $0.0266$ | $0.0533$ | **0.84** | **YES (Left only)** | Valid | **Highly localized.** Right shoulder displacement is exactly $0.000\text{ m}$. Clean deltoid cap. |
| `r-upperarm-shoulder-muscle-incr` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Right Shoulder | $0.0266$ | $0.0533$ | **0.84** | **YES (Right only)** | Valid | **Highly localized.** Left shoulder displacement is exactly $0.000\text{ m}$. Clean deltoid cap. |
| `measure-shoulder-dist-incr` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Shoulders (Bilateral) | $0.0306$ | $0.0612$ | **1.12** | Symmetric | Valid | Widens biacromial distance; slight, acceptable falloff into clavicular junction. |
| `breast-point-incr` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Torso / Chest | $0.0264$ | $0.0528$ | **1.36** | Symmetric | Valid | Modulates chest apex projection; smooth falloff into anterior ribcage. |
| `breast-dist-incr` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Torso / Chest | $0.0263$ | $0.0527$ | **1.38** | Symmetric | Valid | Adjusts inter-pectoral / inter-breast lateral separation. |
| `hip-waist-up` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Waist | $0.0291$ | $0.0583$ | **1.47** | Symmetric | Valid | Translates narrowest waistline position vertically along $Z$-axis. |
| `stomach-pregnant-incr` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Abdomen / Belly | $0.0278$ | $0.0557$ | **1.53** | Symmetric | Valid | **Crucial for Honest Fit.** Forward sagitta-expansion of belly without widening hips. |
| `l-lowerarm-scale-depth-incr` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Left Forearm | $0.0263$ | $0.0526$ | **0.00** | **YES (Left only)** | Valid | **Purely local.** Deepens left forearm cross-section; zero displacement on torso/right arm. |
| `r-lowerarm-scale-depth-incr` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Right Forearm | $0.0263$ | $0.0526$ | **0.00** | **YES (Right only)** | Valid | **Purely local.** Deepens right forearm cross-section; zero displacement on torso/left arm. |
| `l-lowerarm-fat-incr` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Left Forearm | $0.0263$ | $0.0526$ | **0.00** | **YES (Left only)** | Valid | Soft-tissue dilation on left forearm. |
| `r-lowerarm-fat-incr` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Right Forearm | $0.0263$ | $0.0526$ | **0.00** | **YES (Right only)** | Valid | Soft-tissue dilation on right forearm. |
| `buttocks-volume-incr` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Hips / Gluteal | $0.0263$ | $0.0526$ | **1.52** | Symmetric | Valid | Posterior gluteal projection; smooth transition to upper hamstring. |
| `hip-trans-out` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Hips / Trochanter | $0.0275$ | $0.0551$ | **1.53** | Symmetric | Valid | Lateral hip flare; increases trochanteric breadth. |
| `l-upperleg-fat-incr` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Left Thigh | $0.0263$ | $0.0526$ | **4.04** | **YES (Left only)** | Valid | **INSUFFICIENTLY LOCALIZED.** Dilates thigh but causes noticeable bulge in adjacent pelvic fold. |
| `r-upperleg-fat-incr` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Right Thigh | $0.0263$ | $0.0526$ | **4.04** | **YES (Right only)** | Valid | **INSUFFICIENTLY LOCALIZED.** Same pelvic fold spillover on right side. |
| `measure-calf-circ-incr` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Calves | $0.0262$ | $0.0525$ | **2.02** | Symmetric | Valid | Dilates gastrocnemius belly; slight transition into popliteal fossa. |
| `measure-lowerleg-height-incr` | Local | $[-1, 1]$ | $[-0.5, 0.5, -1, 1]$ | Calves / Tibia | $0.0392$ | $0.0785$ | **1.67** | Symmetric | Valid | Lengthens tibia segment; shifts knee joint upward. |

---

## 4. Identification of Insufficiently Localized Controls

The quantitative spillover audit identified one specific control category with high spillover:
- **`l-upperleg-fat-incr` and `r-upperleg-fat-incr` (Spillover Ratio: $4.04$):**
  - **Issue:** Increasing upper leg fat not only expands the thigh cylinder, but also pulls on vertices in the lower pelvic basin and groin fold. At extreme value ($+1.0$), this produces an unnatural bulge in the inguinal crease.
  - **Engineering Resolution for Phase 3 (BICE):**
    1. Clamp the allowed range in the WearWise UI to $[-0.5, +0.5]$.
    2. In the calibration optimizer, apply a targeted locality regularization weight $\lambda_l$ that penalizes displacement of pelvic vertex indices when adjusting thigh parameters.

---

## 5. UI Policy & Abstraction Architecture

> [!IMPORTANT]
> **No Raw Morph Parameters in the Consumer UI:**
> 1. **Zero Ethnic Controls:** Anny includes artist-authored ethnicity morph targets (`african`, `asian`, `caucasian`). In accordance with WearWise core policy, **these must never appear as sliders in the consumer interface**.
> 2. **BICE Abstraction Layer:** Users must never interact directly with raw parameter names like `stomach-pregnant-incr` or `measure-shoulder-dist-incr`. The frontend will present user-friendly regional sliders (e.g. *Shoulder Width*, *Belly Profile*, *Arm Fullness*), and the BICE engine will deterministically map those sliders to the underlying Anny blendshape weights.
