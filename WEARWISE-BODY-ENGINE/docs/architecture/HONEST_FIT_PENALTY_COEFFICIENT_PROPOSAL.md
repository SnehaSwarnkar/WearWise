# WearWise — Honest Fit Penalty Coefficient & Scoring Policy Proposal

**Project:** WearWise AI Fashion & Honest Fit Platform  
**Document:** Honest Fit Mathematical Penalty Coefficient Proposal (HFE-PROP-001)  
**Revision:** 1.1.0 (Harmonized Category Weights, Denominator Normalization & Worked Sensitivity Examples)  
**Date:** 2026-11-23  
**Status:** Approved Provisional Engineering Architecture  
**Authority:** Antigravity (Execution Agent) to ChatGPT (Technical Decision Owner & Product Architect)  

---

## 1. Purpose & Motivation

In accordance with `HONEST_FIT_ENGINE_SPEC.md` Rev 1.2.1 Section 4.1, the composite fit score $S(s) \in [0.0, 100.0]$ is computed via a normalized weighted penalty formulation:

$$S(s) = \max\left(0.0, \; 100.0 - \sum_{k \in \mathcal{K}_{\text{eval}}} \frac{w_k'}{\sum_{j \in \mathcal{K}_{\text{eval}}} w_j'} \cdot \text{Penalty}_k(\text{Ease}_{s, k}, \text{Silhouette})\right)$$

Where $\text{Penalty}_k$ is a bounded quadratic loss penalizing deviation from the user's preferred silhouette ease interval $[\text{TargetLow}_k, \text{TargetHigh}_k)$:

$$\text{Penalty}_k(\text{Ease}) = \min\left(100.0, \; \beta_k \cdot d_k^2\right)$$

$$d_k = \max(0.0, \; \text{TargetLow}_k - \text{Ease}_k, \; \text{Ease}_k - \text{TargetHigh}_k)$$

The approved provisional symmetric penalty coefficients for engineering use are:
- **Chest Circumference:** $\beta_{\text{chest}} = 2.0\text{ cm}^{-2}$
- **Waist Circumference:** $\beta_{\text{waist}} = 2.0\text{ cm}^{-2}$
- **Hip Circumference:** $\beta_{\text{hip}} = 2.0\text{ cm}^{-2}$
- **Shoulder Seam Width:** $\beta_{\text{shoulder}} = 12.0\text{ cm}^{-2}$
- **Torso Length:** $\beta_{\text{length}} = 2.0\text{ cm}^{-2}$

> [!WARNING]
> **Provisional Engineering Designation:** These coefficients are approved for **provisional engineering baseline use** and are not scientifically calibrated. Calibration will be conducted during the Phase 5 empirical wear trials.

This updated proposal:
1. Reconciles the authoritative category-specific baseline and effective weighting policies (clarifying hip weighting in bottoms vs tops).
2. Clarifies denominator normalization $\sum_{j \in \mathcal{K}_{\text{eval}}} w_j'$ and reconciles the sensitivity table with actual composite scores.
3. Provides full worked numerical examples for the T-shirt ($0.70$ denominator) and casual shirt ($0.90$ denominator) pipelines.
4. Integrates the garment measurement provenance standard and fabric tensile property decoupling.

---

## 2. Authoritative Category-Specific Weight Policy & Denominator Handling

Apparel categories require distinct baseline weight allocations. To ensure mathematical consistency across scoring and evidence coverage, the engine enforces one authoritative category policy:

### 2.1 Category Weight Matrix

| Garment Category | Anatomical Dimension ($k$) | Baseline Weight $w_k$ | Assessment State | Effective Weight Discount | Effective Weight $w_k'$ | Role in Category |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **`t_shirt` / `polo`** | `chest_circumference` | $0.40$ | `ELIGIBLE` | $1.0\times$ | **$0.40$** | Required Core |
| | `shoulder_biacromial_breadth` | $0.30$ | `ELIGIBLE` | $1.0\times$ | **$0.30$** | Required Core |
| | `torso_length` | $0.10$ | `UNASSESSED` (Unavailable) | $0.0\times$ | **$0.00$** | Required Core (Coverage check) |
| | `waist_planar_circumference` | $0.20$ | `ELIGIBLE` | $1.0\times$ | **$0.20$** | Optional / Refinement (when supplied) |
| **`casual_shirt` / `dress_shirt`** | `chest_circumference` | $0.40$ | `ELIGIBLE` | $1.0\times$ | **$0.40$** | Required Core |
| | `shoulder_biacromial_breadth` | $0.30$ | `ELIGIBLE` | $1.0\times$ | **$0.30$** | Required Core |
| | `waist_planar_circumference` | $0.20$ | `ELIGIBLE` | $1.0\times$ | **$0.20$** | Required Core |
| | `torso_length` | $0.10$ | `UNASSESSED` (Unavailable) | $0.0\times$ | **$0.00$** | Required Core (Coverage check) |
| **`trousers` / `jeans`** | `waist_planar_circumference` | $0.40$ | `ELIGIBLE` | $1.0\times$ | **$0.40$** | Required Core |
| | `hip_circumference` | $0.40$ | `PROVISIONAL` | $0.5\times$ | **$0.20$** | Required Core |
| | `leg_thigh_circumference` | $0.20$ | `UNASSESSED` (Unavailable) | $0.0\times$ | **$0.00$** | Required Core |

### 2.2 Hip Weighting Reconciliation
- **Bottoms (`trousers`, `jeans`):** The baseline weight is **$w_{\text{hip}} = 0.40$**. Because `hip_circumference` currently carries an assessment state of `PROVISIONAL` from Anny landmark extraction, its effective weight receives the approved $0.5\times$ discount:
  $$w_{\text{hip}}' = 0.5 \times 0.40 = 0.20$$
  Earlier drafts referenced $0.20$ as the baseline weight; this is now formally clarified as the *effective discounted weight*, with the authoritative baseline weight established at $0.40$.
- **Tops (`t_shirt`, `casual_shirt`):** Hip circumference is not part of the standard core specification and carries $w_k = 0.0$ unless a garment specifically defines hem sweep.

### 2.3 Denominator Policies
The engine distinguishes between two distinct denominators:

1. **Evidence Coverage Ratio Denominator:**
   $$C(s) = \frac{\sum_{k \in \mathcal{K}_{\text{eval}}} w_k'}{\sum_{k \in \mathcal{K}_{\text{required}}} w_k}$$
   The denominator is the sum of full baseline weights for all required dimensions for that category:
   - For T-shirt: $\sum_{\text{required}} w_k = 0.40 \text{ (chest)} + 0.30 \text{ (shoulder)} + 0.10 \text{ (length)} = 0.80$.
   - For Casual Shirt: $\sum_{\text{required}} w_k = 0.40 + 0.30 + 0.20 + 0.10 = 1.00$.
   - For Trousers: $\sum_{\text{required}} w_k = 0.40 + 0.40 + 0.20 = 1.00$.

2. **Composite Score Normalization Denominator:**
   $$W_{\text{eval}} = \sum_{j \in \mathcal{K}_{\text{eval}}} w_j'$$
   The denominator strictly sums the *effective weights of evaluated dimensions*, ensuring that the normalized regional weights sum to $1.0$:
   $$\sum_{k \in \mathcal{K}_{\text{eval}}} \frac{w_k'}{W_{\text{eval}}} = 1.000$$
   - In a T-shirt where chest ($0.40$) and shoulders ($0.30$) are evaluated: $W_{\text{eval}} = 0.70$.
     Normalized weights: Chest $= \frac{0.40}{0.70} = \frac{4}{7} \approx 57.14\%$, Shoulders $= \frac{0.30}{0.70} = \frac{3}{7} \approx 42.86\%$.
   - In a casual shirt where chest ($0.40$), shoulders ($0.30$), and waist ($0.20$) are evaluated: $W_{\text{eval}} = 0.90$.
     Normalized weights: Chest $= \frac{0.40}{0.90} = \frac{4}{9} \approx 44.44\%$, Shoulders $= \frac{0.30}{0.90} = \frac{3}{9} \approx 33.33\%$, Waist $= \frac{0.20}{0.90} = \frac{2}{9} \approx 22.22\%$.

---

## 3. Dimensional Scaling Rationale ($\beta_{\text{shoulder}} = 12.0$ vs $\beta_{\text{circ}} = 2.0$)

The quadratic coefficient scales inversely with the square of the regional tier width:

$$\beta_k \propto \frac{1}{\Delta_k^2}$$

- **Circumferential Dimensions (`chest`, `waist`, `hip`):**
  Interval width is $\Delta_{\text{circ}} \approx 6.0\text{ cm}$ (e.g. `REGULAR` $[+6, +12)\text{ cm}$).  
  At a 1-tier shift ($d = 6.0\text{ cm}$), penalty is:
  $$\text{Penalty}_{\text{circ}} = 2.0 \times 6.0^2 = 72.0\text{ points}$$
- **Linear Shoulder Breadth (`shoulder_biacromial_breadth`):**
  Linear bone-to-bone span with interval width $\Delta_{\text{shoulder}} \approx 2.5\text{ cm}$ (e.g. `REGULAR` $[+1.5, +3.5)\text{ cm}$).  
  At a 1-tier shift ($d = 2.5\text{ cm}$), penalty is:
  $$\text{Penalty}_{\text{shoulder}} = 12.0 \times 2.5^2 = 75.0\text{ points}$$

Because $(6.0 / 2.5)^2 = 5.76 \approx 12.0 / 2.0 = 6.0$, a $1\text{ cm}$ shoulder deviation incurs roughly $6\times$ the penalty of a $1\text{ cm}$ chest deviation, reflecting equal perceptual degradation across dimensional modalities.

---

## 4. Reconciled Sensitivity Analysis & Worked Denominator Examples

### 4.1 Regional Penalty vs. Normalized Score Response

The table below reconciles the raw regional penalty with actual normalized score impact across both T-shirt and Casual Shirt denominator regimes:

| Deviation $d$ ($\text{cm}$) | Chest Penalty ($\beta=2.0$) | Shoulder Penalty ($\beta=12.0$) | Waist Penalty ($\beta=2.0$) | T-Shirt Score Impact: Chest Only ($W_{\text{eval}}=0.70$) | T-Shirt Score Impact: Shoulder Only ($W_{\text{eval}}=0.70$) | Casual Shirt Score: Chest Only ($W_{\text{eval}}=0.90$) | Casual Shirt Score: Waist Only ($W_{\text{eval}}=0.90$) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **$0.00$** | **$0.00$** | **$0.00$** | **$0.00$** | **$100.0$** | **$100.0$** | **$100.0$** | **$100.0$** |
| **$0.50$** | **$0.50$** | **$3.00$** | **$0.50$** | $99.7$ | $98.7$ | $99.8$ | $99.9$ |
| **$1.00$** | **$2.00$** | **$12.00$** | **$2.00$** | $98.9$ | $94.9$ | $99.1$ | $99.6$ |
| **$1.50$** | **$4.50$** | **$27.00$** | **$4.50$** | $97.4$ | $88.4$ | $98.0$ | $99.0$ |
| **$2.00$** | **$8.00$** | **$48.00$** | **$8.00$** | $95.4$ | $79.4$ | $96.4$ | $98.2$ |
| **$2.50$** | **$12.50$** | **$75.00$** | **$12.50$** | $92.9$ | $67.9$ | $94.4$ | $97.2$ |
| **$2.89$** | $16.70$ | **$100.00$** | $16.70$ | $90.5$ | $57.1$ | $92.6$ | $96.3$ |
| **$4.00$** | **$32.00$** | **$100.00$** | **$32.00$** | $81.7$ | $57.1$ | $85.8$ | $92.9$ |
| **$5.00$** | **$50.00$** | **$100.00$** | **$50.00$** | $71.4$ | $57.1$ | $77.8$ | $88.9$ |
| **$6.00$** | **$72.00$** | **$100.00$** | **$72.00$** | $58.9$ | $57.1$ | $68.0$ | $84.0$ |
| **$7.07$** | **$100.00$** | **$100.00$** | **$100.00$** | $42.9$ | $57.1$ | $55.6$ | $77.8$ |

*Note: Single-zone score impact is calculated as $100.0 - \frac{w_k'}{W_{\text{eval}}} \cdot \text{Penalty}_k$. For example, in a T-shirt, maximum chest penalty ($100.0$) reduces the score by $\frac{0.40}{0.70} \times 100.0 = 57.14$, yielding $S = 42.9$. Maximum shoulder penalty reduces the score by $\frac{0.30}{0.70} \times 100.0 = 42.86$, yielding $S = 57.1$.*

---

### 4.2 Worked Multi-Zone Numerical Examples

#### Example 1: T-Shirt Size XS on Neutral Masculine Avatar
- **User Preference:** `REGULAR` fit (Target intervals: Chest $[6.0, 12.0)\text{ cm}$, Shoulders $[1.5, 3.5)\text{ cm}$).
- **Body Measurements:** Chest $77.85\text{ cm}$, Shoulders $37.20\text{ cm}$.
- **Garment Finished Dimensions:** Half-chest $41.5\text{ cm}$ ($83.0\text{ cm}$ full circ), Shoulder seam $37.5\text{ cm}$.
- **Ease Calculation:**
  - Chest Ease: $83.00 - 77.85 = +5.15\text{ cm}$ (Falls in `FITTED` $[2.0, 6.0)$).
  - Shoulder Ease: $37.50 - 37.20 = +0.30\text{ cm}$ (Falls in `FITTED` $[-1.0, 1.5)$).
- **Deviation from Preferred Target:**
  - Chest: $d_{\text{chest}} = 6.00 - 5.15 = 0.85\text{ cm}$.
  - Shoulders: $d_{\text{shoulder}} = 1.50 - 0.30 = 1.20\text{ cm}$.
- **Regional Penalty Calculation:**
  - $\text{Penalty}_{\text{chest}} = 2.0 \times 0.85^2 = 2.0 \times 0.7225 = 1.445 \approx 1.45$.
  - $\text{Penalty}_{\text{shoulder}} = 12.0 \times 1.20^2 = 12.0 \times 1.44 = 17.28$.
- **Denominator & Weight Normalization:**
  - $W_{\text{eval}} = w_{\text{chest}}' + w_{\text{shoulder}}' = 0.40 + 0.30 = 0.70$.
  - Normalized Chest Weight: $w_{\text{norm, chest}} = \frac{0.40}{0.70} \approx 0.5714$.
  - Normalized Shoulder Weight: $w_{\text{norm, shoulder}} = \frac{0.30}{0.70} \approx 0.4286$.
- **Composite Score:**
  $$S = 100.0 - (0.5714 \times 1.445 + 0.4286 \times 17.28) = 100.0 - (0.8257 + 7.4062) = 100.0 - 8.232 = 91.768 \approx 91.8$$
- **Recommendation Status:** Because $d > 0$ represents a fitted silhouette deviation from the requested `regular`, Size XS is consistently designated **`alternative`** (Score: $91.8 / 100$).

#### Example 2: Casual Shirt Size M on Neutral Masculine Avatar
- **User Preference:** `REGULAR` fit (Chest $[6, 12)$, Waist $[6, 12)$, Shoulders $[1.5, 3.5)$).
- **Body Measurements:** Chest $77.85\text{ cm}$, Waist $65.96\text{ cm}$, Shoulders $37.20\text{ cm}$.
- **Garment Dimensions:** Chest $94.0\text{ cm}$, Waist $80.0\text{ cm}$, Shoulders $42.0\text{ cm}$.
- **Ease & Deviations:**
  - Chest Ease: $94.00 - 77.85 = +16.15\text{ cm} \implies d = 16.15 - 12.0 = 4.15\text{ cm}$.
  - Waist Ease: $80.00 - 65.96 = +14.04\text{ cm} \implies d = 14.04 - 12.0 = 2.04\text{ cm}$.
  - Shoulder Ease: $42.00 - 37.20 = +4.80\text{ cm} \implies d = 4.80 - 3.5 = 1.30\text{ cm}$.
- **Penalties:**
  - $\text{Penalty}_{\text{chest}} = \min(100.0, 2.0 \times 4.15^2) = 34.445$.
  - $\text{Penalty}_{\text{waist}} = \min(100.0, 2.0 \times 2.04^2) = 8.323$.
  - $\text{Penalty}_{\text{shoulder}} = \min(100.0, 12.0 \times 1.30^2) = 20.280$.
- **Denominator:**
  - $W_{\text{eval}} = 0.40 + 0.30 + 0.20 = 0.90$.
- **Composite Score:**
  $$S = 100.0 - \left(\frac{0.40}{0.90} \times 34.445 + \frac{0.30}{0.90} \times 20.280 + \frac{0.20}{0.90} \times 8.323\right) = 100.0 - (15.309 + 6.760 + 1.850) = 100.0 - 23.919 = 76.081 \approx 76.1$$
- **Recommendation Status:** Designated **`alternative`** (Score: $76.1 / 100$, Relaxed alternative to regular).

---

## 5. Garment Measurement Provenance & Physical Stretch Decoupling

To prevent unverified claims of physical laboratory validation, all garment input dimensions must carry strict provenance metadata:

### 5.1 Provenance Schema (`GarmentMeasurementProvenance`)
- **`sample_id`:** Unique sample or fixture tracking identifier (e.g. `WW-FIXTURE-TSHIRT-2026-001`).
- **`data_origin`:** Categorical origin:
  - `demonstration_fixture`: Engineering reference values formulated for test repeatability.
  - `physical_sample_measured`: Physical garment measured with calibrated instruments.
  - `brand_size_specification`: Nominal dimensions extracted from merchant size chart.
- **`measuring_instrument`:** Specific tool (e.g. `calibrated_rigid_steel_tape_iso_standard`).
- **`measurement_procedure`:** Procedure standard (e.g. `flat_relaxed_tabletop_bs_4952`).
- **`measurement_date`:** ISO 8601 capture date (`2026-11-23`).
- **`operator_id`:** Authenticated measuring technician or automated pipeline identifier.
- **`validation_claim`:** Explicit claim qualifier (e.g. `demonstration_fixture_provisional_not_certified`).

### 5.2 Decoupling Mechanical Stretch from Fibre Composition
Chemical composition ($100\%$ cotton vs $98\%$ cotton / $2\%$ elastane) does not equal physical elasticity. The domain model separates chemical content from physical tensile properties:
- **`fibre_composition`:** `{"cotton": 1.0}`
- **`mechanical_stretch_pct`:** $0.015$ ($1.5\%$ tensile extension under standard $15.0\text{ N}$ load per **BS 4952 / ASTM D3107**).
- **`stretch_recovery_pct`:** $0.90$ ($90\%$ immediate recovery).
- **`stretch_direction`:** `rigid_zero` ($< 2\%$ stretch).

---

## 6. Recommendation

The symmetric penalty coefficients:
$$\beta_{\text{chest}} = 2.0, \quad \beta_{\text{shoulder}} = 12.0, \quad \beta_{\text{waist}} = 2.0, \quad \beta_{\text{hip}} = 2.0, \quad \beta_{\text{length}} = 2.0$$
are accepted as the approved **provisional engineering baselines** for Phase 5A, with the denominator normalization, category weight matrix, and single-top-recommendation policy fully synchronized across code, tests, and documentation.
