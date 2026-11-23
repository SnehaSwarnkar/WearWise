# WearWise Honest Fit Engine Design Specification

**Project:** WearWise AI Fashion & Honest Fit Platform  
**Document:** Honest Fit Engine Specification (HFE-001)  
**Revision:** 1.2.1 (Category Registry Alignment, Fabric Stretch Standards & Discounted Coverage)  
**Date:** 2026-11-23  
**Status:** Approved Technical Architecture  

---

## 1. Executive Purpose & Honest Fit Philosophy

Traditional e-commerce fashion suffers from vanity sizing, inconsistent brand charts, and high return rates ($30\text{--}40\%$). Sizing labels (e.g. "Medium") have no universal physical standard.

The **Honest Fit Engine** replaces arbitrary sizing labels with **transparent dimensional ease comparison**:
1. It compares a customer's normalized body measurements directly against the physical finished dimensions of a garment.
2. It calculates **dimensional ease** for every critical garment zone (chest, waist, hips, shoulders, length) using a verified measurement compatibility registry.
3. It translates mathematical ease deltas into human-understandable fit classifications and explanations using non-overlapping intervals and bounded scoring.

---

## 2. Garment Domain Entities & Measurement Compatibility Registry

### 2.1 Supported Measurement Sets by Garment Category
Apparel categories require distinct dimensional baselines. To maintain absolute consistency between the fit engine and available body measurements extracted in `ANTHROPOMETRY_SPECIFICATION.md`, categories and dimensions are partitioned into Phase 1 supported sets and Phase 5 deferred sets:

| Garment Category | Phase 1 Status | Required Core Measurements ($\mathcal{K}_{\text{required}}$) | Optional / Refinement Measurements | Deferred Dimensions (Phase 5) |
|---|---|---|---|---|
| `t_shirt` / `polo` | **Fully Supported** | `garment_chest_circumference`, `garment_shoulder_seam_width`, `garment_back_length` | `garment_half_chest_width`, `garment_half_waist_width` | `garment_sleeve_length`, `garment_bicep_width` (Phase 5) |
| `casual_shirt` / `dress_shirt` | **Partially Supported** | `garment_chest_circumference`, `garment_waist_circumference`, `garment_shoulder_seam_width`, `garment_back_length` | `garment_half_chest_width`, `garment_half_waist_width` | `garment_neck_circumference` (Deferred: requires C7-thyroid notch loop); `garment_sleeve_length` (Phase 5) |
| `trousers` / `jeans` | **Partially Supported** | `garment_waist_circumference`, `garment_hip_circumference`, `garment_thigh_circumference` | `garment_half_waist_width` | `garment_inseam_length`, `garment_front_rise`, `garment_leg_opening` (Deferred: requires vertical crotch-to-ankle loop tracking) |

### 2.2 Measurement Compatibility Registry
Garment dimensions and body measurements cannot be subtracted naively without transformation. Every dimension in the registry is explicitly mapped to a canonical body measurement from `ANTHROPOMETRY_SPECIFICATION.md` or labeled as deferred:

| Garment Dimension Code | Canonical Body Measurement Code | Dimension Transformation Rule | Tailoring Interpretation | Calibration Status |
|---|---|---|---|---|
| `garment_chest_circumference` | `chest_circumference` | Identity ($1.0 \times \text{value}$) | Horizontal chest girth at nipple apex | **Provisional** |
| `garment_half_chest_width` | `chest_circumference` | Double flat width: $\text{circ} = 2.0 \times \text{width}$ | Pit-to-pit flat garment measurement doubled | **Provisional** |
| `garment_waist_circumference` | `waist_planar_circumference` | Identity ($1.0 \times \text{value}$) | Waistband inner circumference | **Provisional** |
| `garment_half_waist_width` | `waist_planar_circumference` | Double flat width: $\text{circ} = 2.0 \times \text{width}$ | Flat waistband measurement doubled | **Provisional** |
| `garment_hip_circumference` | `hip_circumference` | Identity ($1.0 \times \text{value}$) | Seat / hip girth at maximal seat level | **Provisional** |
| `garment_thigh_circumference` | `leg_thigh_circumference` | Identity ($1.0 \times \text{value}$) | Upper leg girth below gluteal fold | **Provisional** |
| `garment_shoulder_seam_width` | `shoulder_biacromial_breadth` | Tailoring offset (Conventional vs Drop) | Seam position relative to acromion bone | **Provisional** |
| `garment_back_length` | `torso_length` | Vertical coverage check (Coverage $\Delta$) | Garment vertical hem position below crotch | **Provisional** |
| `garment_neck_circumference` | *None (Deferred)* | *Deferred to Phase 5* | Tailored shirting collar band girth | **Deferred (Phase 5)** |
| `garment_inseam_length` | *None (Deferred)* | *Deferred to Phase 5* | Crotch seam to trouser bottom hem | **Deferred (Phase 5)** |

### 2.3 Shoulder Seam Mapping & Garment Construction
- **Conventional Set-In Sleeve:** The shoulder seam is designed to sit directly on the acromial bone process ($\text{Seam Offset} = G_{\text{shoulder}} - B_{\text{biacromial}} \in [-1.0, +1.5\text{ cm}]$).
- **Drop-Shoulder / Streetwear:** The shoulder seam is intentionally engineered to hang past the acromion down onto the upper arm ($\text{Seam Offset} \in [+3.0, +8.0\text{ cm}]$). The engine uses garment silhouette metadata to avoid falsely penalizing intentional drop shoulders as "too large".

### 2.4 Vertical Length Coverage vs. Circumferential Ease
Garment length (`garment_back_length`) is a **vertical coverage check**, not an enclosed girth. It does not constrain the wearer circumscribingly:
$$\text{CoverageDelta} = G_{\text{back\_length}} - B_{\text{torso\_length}}$$
Positive values indicate the hem extends below the crotch line; negative values indicate cropped styling.

### 2.5 Fabric Mechanical Properties & Physical Testing Standards
Elastane percentage ($2\%$) does **not** equal mechanical stretch. The domain model decouples chemical fibre composition from physical stretch response:
- **`fibre_composition`:** Dict of fabric content, e.g. `{"cotton": 0.98, "elastane": 0.02}`.
- **Physical Test Standards:**
  - **Woven Stretch Fabrics:** Tested per **BS 4952 / ASTM D3107** ("Standard Test Methods for Stretch Properties of Fabrics Woven from Stretch Yarns") and **ISO 20932-1** ("Determination of the elasticity of fabrics — Part 1: Strip tests").
  - **Knitted Fabrics:** Tested per **ASTM D2594** ("Standard Test Method for Stretch Properties of Knitted Fabrics Having Low Power") and **ISO 20932-2** ("Part 2: Multiaxial tests").
- **Standard Test Procedure:**
  - **Specimen:** $100\text{ mm} \times 50\text{ mm}$ strip specimen with $100\text{ mm}$ gauge length.
  - **Standard Load:** $15.0\text{ N}$ for lightweight knits and jerseys; $30.0\text{ N}$ for stretch wovens and denim.
  - **Conditioning:** ISO 139 standard atmosphere ($20.0^\circ\text{C} \pm 2.0^\circ\text{C}$, $65\% \pm 4\%\text{ RH}$).
  - **Measured Metrics:**
    - `mechanical_stretch_pct`: Extension percentage under standard load ($E_{\text{load}}\%$, e.g. $0.045$ for $4.5\%$).
    - `stretch_recovery_pct`: Immediate elastic recovery after $1\text{ min}$ ($R_{\text{imm}}\%$, e.g. $0.92$ for $92\%$) and delayed recovery after $30\text{ min}$ ($R_{\text{del}}\%$).
- **`stretch_direction`:** `Literal["rigid_zero", "mono_weft", "mono_warp", "bi_directional_four_way"]`.
- **Provisional Classification Consistency Rules:**
  - `rigid_zero`: `mechanical_stretch_pct < 0.02` ($< 2\%$).
  - `rigid_low`: `0.02 <= mechanical_stretch_pct < 0.05` ($2\% - 5\%$).
  - `stretch_moderate`: `0.05 <= mechanical_stretch_pct < 0.15` ($5\% - 15\%$).
  - `stretch_high`: `mechanical_stretch_pct >= 0.15` ($> 15\%$).
  *(Note: Classification thresholds are provisional engineering baselines pending Phase 5 fabric tensile bench testing).*

---

## 3. The Dimensional Ease Model & 6-Tier Non-Overlapping Classification

### 3.1 Mathematical Formulation of Ease
For any circumferential measurement code $k \in \mathcal{K}$:
$$\text{Ease}_k = G_k - B_k$$
Where $G_k$ is the garment finished dimension ($\text{cm}$) and $B_k$ is the user's active body dimension ($\text{cm}$).

### 3.2 Non-Overlapping Fit Spectrum (6 Distinct Classes)
To eliminate boundary ambiguity, regional classifications are defined using **half-open intervals $[a, b)$**:

```python
from enum import Enum

class RegionalFitClassification(str, Enum):
    TOO_TIGHT = "too_tight"       # Ease < Lower_fitted (Constricting / unwearable)
    FITTED = "fitted"             # [Lower_fitted, Upper_fitted) (Tailored silhouette)
    REGULAR = "regular"           # [Lower_regular, Upper_regular) (Standard daily comfort)
    RELAXED = "relaxed"           # [Lower_relaxed, Upper_relaxed) (Casual loose silhouette)
    OVERSIZED = "oversized"       # [Lower_oversized, Upper_oversized) (Streetwear / drop-shoulder)
    TOO_LARGE = "too_large"       # Ease >= Upper_oversized (Excessive volume / poor fit)
```

### 3.3 Provisional Ease Threshold Rulebook (Crewneck T-Shirt Baseline)

> [!WARNING]
> **Provisional Engineering Baseline:** The ease boundaries below are **PROVISIONAL** baselines derived from classical tailoring standards. They must **never be claimed as finalized or validated** until the physical garment trials scheduled in **Phase 5**.

| Anatomical Dimension ($k$) | TOO_TIGHT ($<$) | FITTED $[a, b)$ | REGULAR $[a, b)$ | RELAXED $[a, b)$ | OVERSIZED $[a, b)$ | TOO_LARGE ($\ge$) |
|---|---|---|---|---|---|---|
| `chest_circumference` | $< +2.0\text{ cm}$ | $[+2.0, +6.0\text{ cm})$ | $[+6.0, +12.0\text{ cm})$ | $[+12.0, +18.0\text{ cm})$ | $[+18.0, +24.0\text{ cm})$ | $\ge +24.0\text{ cm}$ |
| `waist_planar_circumference` | $< +2.0\text{ cm}$ | $[+2.0, +6.0\text{ cm})$ | $[+6.0, +12.0\text{ cm})$ | $[+12.0, +18.0\text{ cm})$ | $[+18.0, +24.0\text{ cm})$ | $\ge +24.0\text{ cm}$ |
| `shoulder_biacromial_breadth` | $< -1.0\text{ cm}$ | $[-1.0, +1.5\text{ cm})$ | $[+1.5, +3.5\text{ cm})$ | $[+3.5, +6.0\text{ cm})$ | $[+6.0, +9.0\text{ cm})$ | $\ge +9.0\text{ cm}$ |
| `torso_length` (Coverage $\Delta$) | $< -4.0\text{ cm}$ | $[-4.0, +0.0\text{ cm})$ | $[+0.0, +6.0\text{ cm})$ | $[+6.0, +12.0\text{ cm})$ | $[+12.0, +18.0\text{ cm})$ | $\ge +18.0\text{ cm}$ |

---

## 4. Normalized Composite Fit Scoring & Recommendation Logic

### 4.1 Mathematically Bounded Scoring Formulation
For an evaluated garment size $s$, the composite fit score $S(s) \in [0.0, 100.0]$ is strictly normalized by the sum of effective weights of assessed dimensions:

$$S(s) = \max\left(0.0, \; 100.0 - \sum_{k \in \mathcal{K}_{\text{eval}}} \frac{w_k'}{\sum_{j \in \mathcal{K}_{\text{eval}}} w_j'} \cdot \text{Penalty}_k(\text{Ease}_{s, k}, \text{Silhouette})\right)$$

Where:
- $\mathcal{K}_{\text{eval}}$ is the set of compatible measurements available for both user and garment that are in `assessment_state == 'eligible'` or `'provisional'`.
- $w_k$ is the regional baseline importance weight (e.g. Chest: $0.40$, Shoulders: $0.30$, Waist: $0.20$, Length: $0.10$).
- **Effective Weight Calculation ($w_k'$):**
  $$w_k' = \begin{cases} 1.0 \times w_k & \text{if } \text{assessment\_state} = \text{'eligible'} \\ 0.5 \times w_k & \text{if } \text{assessment\_state} = \text{'provisional'} \\ 0.0 & \text{if disputed, rejected, or missing} \end{cases}$$
- The denominator strictly normalizes the effective weights $\sum_{j \in \mathcal{K}_{\text{eval}}} w_j'$, ensuring that the weighted penalty coefficients sum strictly to $1.0$, guaranteeing score bounds within $[0.0, 100.0]$.
- Measurements with `validation_state == 'disputed'` or `assessment_state == 'rejected'` have $w_k' = 0.0$ and are completely excluded from $\mathcal{K}_{\text{eval}}$.
- $\text{Penalty}_k$ is a quadratic loss penalizing deviation from the user's preferred silhouette ease interval:
  $$\text{Penalty}_k(\text{Ease}) = \min\left(100.0, \beta_k \cdot \max(0.0, \text{TargetLow}_k - \text{Ease}, \text{Ease} - \text{TargetHigh}_k)^2\right)$$
- If $\text{Ease}_k < \text{MinimumWearable}_k$ in a rigid fabric, $\text{Penalty}_k = 100.0$ (immediate rejection of unwearable tight sizes).

### 4.2 Minimum Evidence Coverage Requirement
To prevent misleading sizing advice based on sparse data, the Evidence Coverage ratio evaluates whether sufficient body dimensions are available:

- **Effective Evidence Coverage Ratio:**
  $$C(s) = \frac{\sum_{k \in \mathcal{K}_{\text{eval}}} w_k'}{\sum_{k \in \mathcal{K}_{\text{required}}} w_k}$$
  Where the numerator sums the discounted effective weights $w_k'$ (giving provisional measurements half weight), and the denominator sums the full baseline weights $w_k$ of all required core dimensions for that garment category.
- **Coverage Gate Rule:** A sizing recommendation requires $C(s) \ge 0.70$ ($70\%$).
- **Insufficient Evidence State:** If $C(s) < 0.70$, the engine suppresses scoring, returns `status: "insufficient_data"`, and generates an actionable prompt specifying the exact missing dimensions required (e.g. *"Please provide chest circumference to evaluate fit for this crewneck T-shirt"*).

### 4.3 Natural Language Explanation Generator
Explanations are transparent and grounded in centimeters (values such as `94.5` are **illustrative sample scores**, not calibrated benchmarks):
- *"Size L is recommended for your preferred Regular fit (Illustrative Fit Score: 94.5 / 100)."*
- *"Chest has +8.5 cm ease (Standard comfortable room)."*
- *"Shoulder seams sit 2.3 cm past your acromion bone for a relaxed drop."*
- *"Size M is an alternative if you prefer a snug tailored fit (+3.5 cm chest ease)."*

---

## 5. Phase 5 Calibration Gate Requirements

To transition the ease rulebook from `PROVISIONAL` to `CALIBRATED`:
1. Conduct physical wear trials with standard 100% cotton crewneck T-shirts across 5 standard sizes (S to XXL).
2. Measure physical garments with calibrated rigid steel tape using standardized procedures.
3. Record subjective comfort and fit perceptions across 20 test participants to tune interval boundaries.
