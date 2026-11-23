# WearWise — Honest Fit Penalty Coefficient & Scoring Policy Proposal

**Project:** WearWise AI Fashion & Honest Fit Platform  
**Document:** Honest Fit Mathematical Penalty Coefficient Proposal (HFE-PROP-001)  
**Revision:** 1.0.0  
**Date:** 2026-11-23  
**Status:** Architecture Proposal for Technical Review  
**Authority:** Antigravity (Execution Agent) to ChatGPT (Technical Decision Owner & Product Architect)  

---

## 1. Purpose & Motivation

In accordance with `HONEST_FIT_ENGINE_SPEC.md` Rev 1.2.1 Section 4.1, the composite fit score $S(s) \in [0.0, 100.0]$ is computed via a normalized weighted penalty formulation:

$$S(s) = \max\left(0.0, \; 100.0 - \sum_{k \in \mathcal{K}_{\text{eval}}} \frac{w_k'}{\sum_{j \in \mathcal{K}_{\text{eval}}} w_j'} \cdot \text{Penalty}_k(\text{Ease}_{s, k}, \text{Silhouette})\right)$$

Where $\text{Penalty}_k$ is a bounded quadratic loss penalizing deviation from the user's preferred silhouette ease interval $[\text{TargetLow}_k, \text{TargetHigh}_k)$:

$$\text{Penalty}_k(\text{Ease}) = \min\left(100.0, \; \beta_k \cdot d_k^2\right)$$

$$d_k = \max(0.0, \; \text{TargetLow}_k - \text{Ease}_k, \; \text{Ease}_k - \text{TargetHigh}_k)$$

While the mathematical structure of $S(s)$ is strictly defined, the penalty coefficients $\beta_k$ require an explicit, documented policy. Silently choosing arbitrary coefficients risks distorting recommendations or falsely asserting scientific calibration.

This document presents:
1. The mathematical derivation of the proposed baseline provisional coefficients $\beta_k$.
2. The dimensional scaling rationale across circumferences vs. linear breadths.
3. An asymmetric tightness-versus-looseness penalty framework.
4. A sensitivity analysis across deviations $d \in [0.0, 10.0\text{ cm}]$.
5. The Phase 5 empirical calibration protocol to transition from provisional to calibrated status.

---

## 2. Dimensional Tier Width Analysis & $\beta_k$ Derivation

### 2.1 The Principle of Tier-Normalized Sensitivity

In the 6-tier classification spectrum (`TOO_TIGHT`, `FITTED`, `REGULAR`, `RELAXED`, `OVERSIZED`, `TOO_LARGE`), ease boundaries are grouped into discrete regional intervals. 

A consumer requesting a `REGULAR` fit who receives a garment that is $1\text{ cm}$ outside the `REGULAR` interval experiences a minor silhouette deviation. Conversely, a garment that is a full tier away (e.g., in `OVERSIZED` or `TOO_TIGHT`) represents a noticeable fit failure.

Therefore, the penalty should scale such that:
- **Zero Deviation ($d = 0\text{ cm}$):** $\text{Penalty} = 0.0$ (Score = $100.0$).
- **Minor Boundary Drift ($d \approx 1\text{ cm}$ for girths):** $\text{Penalty} \in [2.0, 8.0]$ (Subtle score reduction).
- **Full Tier Deviation ($d = \Delta_{\text{tier}}$):** $\text{Penalty} \approx 70.0\text{--}80.0$ (Strong disincentive, moving the size out of "recommended" into "alternative" or "poor fit").
- **Two Tier Deviation ($d \ge 1.2 \times \Delta_{\text{tier}}$):** $\text{Penalty} = 100.0$ (Complete regional disqualification).

### 2.2 Circumferential Girths (`chest_circumference`, `waist_planar_circumference`, `hip_circumference`)

From `HONEST_FIT_ENGINE_SPEC.md` Table 3.3:
- `FITTED`: $[+2.0, +6.0\text{ cm})$ (Width: $4.0\text{ cm}$)
- `REGULAR`: $[+6.0, +12.0\text{ cm})$ (Width: $6.0\text{ cm}$)
- `RELAXED`: $[+12.0, +18.0\text{ cm})$ (Width: $6.0\text{ cm}$)
- `OVERSIZED`: $[+18.0, +24.0\text{ cm})$ (Width: $6.0\text{ cm}$)

The typical tier width for circumferential dimensions is $\Delta_{\text{circ}} = 6.0\text{ cm}$.

If we designate a full tier shift ($d = 6.0\text{ cm}$) to incur a penalty of $72.0$ points:

$$\beta_{\text{circ}} \cdot (6.0\text{ cm})^2 = 72.0 \implies \beta_{\text{circ}} = \frac{72.0}{36.0} = 2.0\text{ cm}^{-2}$$

Under $\beta_{\text{circ}} = 2.0\text{ cm}^{-2}$:
- $d = 0.0\text{ cm} \implies \text{Penalty} = 0.0$
- $d = 1.0\text{ cm} \implies \text{Penalty} = 2.0$
- $d = 2.0\text{ cm} \implies \text{Penalty} = 8.0$
- $d = 3.0\text{ cm} \implies \text{Penalty} = 18.0$
- $d = 4.0\text{ cm} \implies \text{Penalty} = 32.0$
- $d = 5.0\text{ cm} \implies \text{Penalty} = 50.0$
- $d = 6.0\text{ cm} \implies \text{Penalty} = 72.0$
- $d \ge 7.07\text{ cm} \implies \text{Penalty} = 100.0$ (Saturated cap)

### 2.3 Linear Caliper Breadth (`shoulder_biacromial_breadth`)

Shoulder seam placement is a **linear transverse breadth**, not a circumference. An adult human shoulder breadth is approximately $37\text{ cm}$, whereas chest girth is approximately $78\text{--}100\text{ cm}$ (a ratio of $\approx 2.5\times$).

Consequently, the tailoring intervals for shoulder seam offset are significantly narrower:
- `FITTED`: $[-1.0, +1.5\text{ cm})$ (Width: $2.5\text{ cm}$)
- `REGULAR`: $[+1.5, +3.5\text{ cm})$ (Width: $2.0\text{ cm}$)
- `RELAXED`: $[+3.5, +6.0\text{ cm})$ (Width: $2.5\text{ cm}$)
- `OVERSIZED`: $[+6.0, +9.0\text{ cm})$ (Width: $3.0\text{ cm}$)

The typical tier width for shoulder seam offset is $\Delta_{\text{shoulder}} = 2.5\text{ cm}$.

Applying the same requirement that a full tier shift ($d = 2.5\text{ cm}$) incurs a penalty of $75.0$ points:

$$\beta_{\text{shoulder}} \cdot (2.5\text{ cm})^2 = 75.0 \implies \beta_{\text{shoulder}} = \frac{75.0}{6.25} = 12.0\text{ cm}^{-2}$$

Under $\beta_{\text{shoulder}} = 12.0\text{ cm}^{-2}$:
- $d = 0.0\text{ cm} \implies \text{Penalty} = 0.0$
- $d = 0.5\text{ cm} \implies \text{Penalty} = 3.0$
- $d = 1.0\text{ cm} \implies \text{Penalty} = 12.0$
- $d = 1.5\text{ cm} \implies \text{Penalty} = 27.0$
- $d = 2.0\text{ cm} \implies \text{Penalty} = 48.0$
- $d = 2.5\text{ cm} \implies \text{Penalty} = 75.0$
- $d \ge 2.89\text{ cm} \implies \text{Penalty} = 100.0$ (Saturated cap)

Notice the structural consistency:
$$\frac{\beta_{\text{shoulder}}}{\beta_{\text{circ}}} = \frac{12.0}{2.0} = 6.0 \approx \left(\frac{\Delta_{\text{circ}}}{\Delta_{\text{shoulder}}}\right)^2 = \left(\frac{6.0}{2.5}\right)^2 = 5.76$$

The quadratic penalty coefficient scales inversely with the square of the regional tier width, ensuring equal perceptual sensitivity across dimensional types.

### 2.4 Vertical Coverage (`torso_length`)

For garment back length, the interval width is $6.0\text{ cm}$ per tier ($[0, 6)$, $[6, 12)$, etc.).  
Thus, $\beta_{\text{length}} = 2.0\text{ cm}^{-2}$, identical to circumferential girths.

---

## 3. Asymmetric Tightness vs. Looseness Policy

In garment ergonomics and human wear perception, **tightness and looseness are fundamentally asymmetric**:
1. **Tightness (Constriction):** Physically restricts breathing, mobility, and seam integrity. In non-stretch fabrics, negative ease or insufficient ease makes a garment unwearable.
2. **Looseness (Excess Volume):** A garment that is looser than desired remains wearable; it simply represents a different stylistic silhouette.

### 3.1 Proposed Asymmetric Coefficient Formulation

$$\text{Penalty}_k(\text{Ease}) = \begin{cases}
100.0 & \text{if } \text{Ease}_k < \text{MinimumWearable}_k \text{ and fabric is rigid} \\
\min\left(100.0, \; \beta_k^{\text{tight}} \cdot (\text{TargetLow}_k - \text{Ease}_k)^2\right) & \text{if } \text{Ease}_k < \text{TargetLow}_k \\
0.0 & \text{if } \text{TargetLow}_k \le \text{Ease}_k < \text{TargetHigh}_k \\
\min\left(100.0, \; \beta_k^{\text{loose}} \cdot (\text{Ease}_k - \text{TargetHigh}_k)^2\right) & \text{if } \text{Ease}_k \ge \text{TargetHigh}_k
\end{cases}$$

### 3.2 Recommended Provisional Baseline Values

| Dimension Code ($k$) | Baseline Weight $w_k$ | Typical Tier Width $\Delta_k$ | Minimum Wearable Ease ($\text{cm}$) | Symmetric $\beta_k$ | Asymmetric $\beta_k^{\text{tight}}$ ($1.5\times$) | Asymmetric $\beta_k^{\text{loose}}$ ($1.0\times$) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `chest_circumference` | $0.40$ | $6.0\text{ cm}$ | $+2.0\text{ cm}$ (rigid) | **$2.0$** | **$3.0$** | **$2.0$** |
| `shoulder_biacromial_breadth` | $0.30$ | $2.5\text{ cm}$ | $-1.0\text{ cm}$ (rigid) | **$12.0$** | **$18.0$** | **$12.0$** |
| `waist_planar_circumference` | $0.20$ | $6.0\text{ cm}$ | $+2.0\text{ cm}$ (rigid) | **$2.0$** | **$3.0$** | **$2.0$** |
| `hip_circumference` | $0.20$ | $6.0\text{ cm}$ | $+3.0\text{ cm}$ (rigid) | **$2.0$** | **$3.0$** | **$2.0$** |
| `torso_length` | $0.10$ | $6.0\text{ cm}$ | $-4.0\text{ cm}$ (cropped) | **$2.0$** | **$2.5$** | **$2.0$** |

*Note: For Phase 5A, the engine implements symmetric $\beta_k$ by default, while supporting the asymmetric multipliers via configurable policy.*

---

## 4. Sensitivity Analysis & Boundary Response

### 4.1 Numerical Response Table

The table below illustrates the penalty response and resulting single-dimension score impact across deviations $d \in [0.0, 10.0\text{ cm}]$:

| Deviation $d$ ($\text{cm}$) | Chest Penalty ($\beta=2.0$) | Chest Tier Equivalent | Shoulder Penalty ($\beta=12.0$) | Shoulder Tier Equivalent | Single-Zone Score (Weight $0.40$) |
|:---:|:---:|:---|:---:|:---|:---:|
| **$0.00$** | **$0.00$** | Target Interval | **$0.00$** | Target Interval | **$100.0$** |
| **$0.50$** | **$0.50$** | Barely perceptible drift | **$3.00$** | Slight seam shift | **$99.8$** |
| **$1.00$** | **$2.00$** | Mild boundary bleed | **$12.00$** | Half-tier seam shift | **$99.2$** |
| **$1.50$** | **$4.50$** | Noticeable shift | **$27.00$** | Moderate drop | **$98.2$** |
| **$2.00$** | **$8.00$** | $1/3$ tier shift | **$48.00$** | Approaching full tier | **$96.8$** |
| **$2.50$** | **$12.50$** | Approaching half tier | **$75.00$** | **Full tier shift** | **$95.0$** |
| **$2.89$** | **$16.70$** | Half tier shift | **$100.00$** | **Max shoulder cap** | **$93.3$** |
| **$3.00$** | **$18.00$** | Half tier shift | **$100.00$** (capped) | Saturated | **$92.8$** |
| **$4.00$** | **$32.00$** | $2/3$ tier shift | **$100.00$** (capped) | Saturated | **$87.2$** |
| **$5.00$** | **$50.00$** | Near full tier shift | **$100.00$** (capped) | Saturated | **$80.0$** |
| **$6.00$** | **$72.00$** | **Full tier shift** | **$100.00$** (capped) | Saturated | **$71.2$** |
| **$7.07$** | **$100.00$** | **Max chest cap** | **$100.00$** (capped) | Saturated | **$60.0$** |
| **$8.00$** | **$100.00$** (capped) | Saturated | **$100.00$** (capped) | Saturated | **$60.0$** |
| **$10.00$** | **$100.00$** (capped) | Saturated | **$100.00$** (capped) | Saturated | **$60.0$** |

### 4.2 Key Invariants Observed
1. **Boundedness:** In all cases, $0.0 \le \text{Penalty}_k \le 100.0$ and $0.0 \le S(s) \le 100.0$.
2. **Monotonicity:** $\forall d_1 < d_2 \implies \text{Penalty}_k(d_1) \le \text{Penalty}_k(d_2)$.
3. **Smooth Differentiability Near Zero:** Quadratic growth ($\beta d^2$) produces zero slope at $d = 0$, preventing harsh cliff-edge drops when measurements land near interval boundaries.
4. **Saturation:** Excessive deviations saturate cleanly at $100.0$ without causing numerical divergence or negative composite scores.

---

## 5. Fabric Elasticity Coupling

When a garment contains elastane or mechanical knit stretch ($E_{\text{load}}\% > 0$):
1. **Dynamic Ease Shift:** Fabric stretch effectively expands the permissible ease interval toward smaller numbers:
   $$\text{TargetLow}_k^{\text{stretch}} = \text{TargetLow}_k^{\text{rigid}} - \alpha \cdot (E_{\text{load}}\% \times B_k)$$
   where $\alpha \in [0.3, 0.6]$ is the effective strain coefficient.
2. **Provisional Policy for Phase 5A:**
   For Phase 5A, rigid baselines are enforced ($E_{\text{load}} < 2\%$, rigid zero/low). When stretch fabrics are tested in Phase 5, the lower bounds will adjust dynamically per BS 4952 / ASTM D3107 test values.

---

## 6. Phase 5 Calibration Gate Protocol

To transition these proposed $\beta_k$ values from `PROVISIONAL` to `CALIBRATED`:
1. **Standardized Garments:** Acquire 5 sizes (S, M, L, XL, XXL) of a 100% cotton crewneck T-shirt with verified finished physical dimensions.
2. **Subject Cohort:** Recruit 20 diverse participants with 3D avatars generated from the WearWise pipeline.
3. **Double-Blind Evaluation:**
   - Participants try on 3 sizes (their predicted size, one smaller, one larger).
   - Participants complete a standardized 5-point Likert survey assessing regional tightness, comfort, and silhouette preference.
4. **Optimization:** Fit coefficients $\beta_k$ using maximum likelihood estimation (ordinal logistic regression) against customer preference distributions.

---

## 7. Recommendation

We recommend accepting:
- $\beta_{\text{chest}} = 2.0\text{ cm}^{-2}$
- $\beta_{\text{shoulder}} = 12.0\text{ cm}^{-2}$
- $\beta_{\text{waist}} = 2.0\text{ cm}^{-2}$
- $\beta_{\text{hip}} = 2.0\text{ cm}^{-2}$
- $\beta_{\text{length}} = 2.0\text{ cm}^{-2}$

as the **provisional engineering baselines** for Phase 5A, implemented symmetrically with configurable overrides for empirical tuning.
