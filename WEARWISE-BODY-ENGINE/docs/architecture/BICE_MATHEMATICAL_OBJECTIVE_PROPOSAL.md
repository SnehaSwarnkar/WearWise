# WearWise BICE Mathematical Optimizer Objective Specification

**Project:** WearWise AI Fashion & Honest Fit Platform  
**Document ID:** BICE-OPT-001  
**Revision:** 1.0.0 (Technical Design Checkpoint)  
**Date:** 2026-11-23  
**Authority:** Submitted to ChatGPT (Technical Decision Owner & Product Architect) for Technical Review  
**Status:** PROPOSED — PENDING FORMAL REVIEW & ACCEPTANCE  

---

## 1. Executive Summary & Objective Purpose

The Body Intelligence & Calibration Engine (BICE) mediates between two potentially conflicting inputs:
1. **Physical Anthropometric Ground Truth ($\mathbf{m}^*$):** Customer tape measurements (e.g. chest circumference $104.5\text{ cm}$, waist $86.0\text{ cm}$) with associated tolerances ($\sigma_k$) and reliability weights ($w_k$).
2. **Shopper Semantic Style & Body-Shape Intent ($\mathbf{c}^*$):** Normalized consumer sliders representing visible form adjustments (e.g. `shoulder_width=0.60`, `belly_fullness=0.70`).

Simultaneously, the avatar representation must avoid non-local geometric artifacts (cross-regional mesh spillover) and obey anatomical boundary limits.

This document formally defines the **proposed multi-objective regularized loss function**, weighting coefficients, convergence policies, and safety boundary conditions for the BICE iterative solver.

---

## 2. Mathematical State Representation

Let the avatar shape intent be parameterized by the candidate regional scale vector $\mathbf{s} \in \mathbb{R}^{3K}$, representing scale factors across $K$ anatomical regions ($R \in \mathcal{R}$):

$$\mathbf{s} = \left[ \mathbf{s}_{R_1}^T, \mathbf{s}_{R_2}^T, \dots, \mathbf{s}_{R_K}^T \right]^T, \quad \text{where } \mathbf{s}_R = \begin{bmatrix} s_{R, x} \\ s_{R, y} \\ s_{R, z} \end{bmatrix}$$

Subject to box constraints defined by the regional bounds engine:

$$\mathbf{b}_{R, \min} \le \mathbf{s}_R \le \mathbf{b}_{R, \max}, \quad \forall R \in \mathcal{R}$$

Provisional engineering limits:
- Thighs ($R=\text{thighs}$): $s_{R, x} \in [-0.50, +0.50]$
- Belly ($R=\text{waist\_abdomen}$): $s_{R, y} \in [-0.50, +0.70]$
- Shoulders ($R=\text{shoulders}$): $s_{R, x} \in [-0.75, +0.75]$
- General bounds for unconstrained axes: $s_{R, \alpha} \in [-1.00, +1.00]$

---

## 3. Total Regularized Objective Function

The scalar objective function $\mathcal{J}(\mathbf{s}; \mathbf{m}^*, \mathbf{c}^*)$ to be minimized is formulated as:

$$\mathcal{J}(\mathbf{s}; \mathbf{m}^*, \mathbf{c}^*) = \lambda_{\text{meas}} \mathcal{L}_{\text{meas}}(\mathbf{s}; \mathbf{m}^*) + \lambda_{\text{ctrl}} \mathcal{L}_{\text{ctrl}}(\mathbf{s}; \mathbf{c}^*) + \lambda_{\text{loc}} \mathcal{L}_{\text{locality}}(\mathbf{s}) + \lambda_{\text{reg}} \mathcal{L}_{\text{prior}}(\mathbf{s})$$

Where:
- $\mathcal{L}_{\text{meas}}$: Target anthropometric measurement matching loss.
- $\mathcal{L}_{\text{ctrl}}$: Semantic control preservation loss.
- $\mathcal{L}_{\text{locality}}$: Cross-regional geometric spillover loss.
- $\mathcal{L}_{\text{prior}}$: Tikhonov regularization toward neutral anatomy.
- $\lambda_{\text{meas}}, \lambda_{\text{ctrl}}, \lambda_{\text{loc}}, \lambda_{\text{reg}}$: Non-negative weighting hyperparameters.

---

## 4. Formulation of Objective Terms

### 4.1 Target Anthropometric Measurement Loss ($\mathcal{L}_{\text{meas}}$)

Let $\mathcal{M}$ denote the set of active physical measurements provided for the body profile. For each measurement $k \in \mathcal{M}$:
- $m_k^*$: Target physical value in centimeters.
- $\hat{m}_k(\mathbf{s})$: Estimated physical dimension extracted from candidate shape $\mathbf{s}$ (in cm).
- $\sigma_k$: Measurement uncertainty tolerance in centimeters (`tolerance_cm`, $\sigma_k \ge 0.1\text{ cm}$).
- $w_k$: Reliability policy weight ($w_k \in [0.0, 1.0]$, default $1.00$).

The measurement loss is defined as a normalized, dimensionless squared residual:

$$\mathcal{L}_{\text{meas}}(\mathbf{s}; \mathbf{m}^*) = \frac{1}{|\mathcal{M}|} \sum_{k \in \mathcal{M}} w_k \cdot \left( \frac{\hat{m}_k(\mathbf{s}) - m_k^*}{\sigma_k} \right)^2$$

**Justification:** Dividing by tolerance $\sigma_k$ ensures that measurements with tight verification (e.g. professional tailor tape, $\pm 0.5\text{ cm}$) have four-fold higher gradient pull than unverified self-estimates ($\pm 2.0\text{ cm}$), preventing coarse estimates from overwhelming exact data.

### 4.2 Semantic Control Preservation Loss ($\mathcal{L}_{\text{ctrl}}$)

Let $\mathbf{s}^{\text{init}}(\mathbf{c}^*) = \mathcal{M}_{\text{rules}}(\text{normalize}(\mathbf{c}^*))$ be the deterministic regional scales directly projected from consumer sliders $\mathbf{c}^*$ via `map_controls_to_regional_scales`.

The semantic preservation loss penalizes deviations from the shopper's explicit visual preference:

$$\mathcal{L}_{\text{ctrl}}(\mathbf{s}; \mathbf{c}^*) = \frac{1}{|\mathcal{C}|} \sum_{j \in \mathcal{C}} \left( s_j - s_j^{\text{init}}(\mathbf{c}^*) \right)^2$$

Where $\mathcal{C}$ indexes the active mapped regional scale axes.

**Justification:** Quadratic penalty ensures that the solver minimally modifies user-adjusted sliders only to the extent necessary to satisfy hard anthropometric circumferences.

### 4.3 Geometric Locality Penalty ($\mathcal{L}_{\text{locality}}$)

Locality is evaluated via `ShapeEvaluationPort`. For a target modification in region $R_{\text{target}}$:

$$\text{RMSR}_R(\mathbf{s}) = \frac{\bar{\Delta}_R(\mathbf{s})}{\bar{\Delta}_{R_{\text{target}}}(\mathbf{s})}$$

The locality loss aggregates the maximal spillover across all non-target anatomical zones:

$$\mathcal{L}_{\text{locality}}(\mathbf{s}) = \max_{R \ne R_{\text{target}}} \text{RMSR}_R(\mathbf{s})$$

### 4.4 Prior Regularization ($\mathcal{L}_{\text{prior}}$)

Prevents extreme or degenerate regional deformations by regularizing candidate scales toward neutral morphology ($\mathbf{0}$):

$$\mathcal{L}_{\text{prior}}(\mathbf{s}) = \|\mathbf{s}\|_2^2 = \sum_{R \in \mathcal{R}} \left( s_{R, x}^2 + s_{R, y}^2 + s_{R, z}^2 \right)$$

---

## 5. Provisional Weighting Coefficients

The following hyperparameters are proposed as initial engineering baselines, subject to empirical calibration during Phase 4 integration:

| Parameter | Proposed Value | Functional Purpose |
|---|---|---|
| $\lambda_{\text{meas}}$ | `1.00` | Primary fitting constraint; ensures avatar matches tailoring circumferences. |
| $\lambda_{\text{ctrl}}$ | `0.40` | Preserves visual shape styling without overriding measured tape dimensions. |
| $\lambda_{\text{loc}}$ | `0.70` | Suppresses unwanted secondary deformations in distant anatomical regions. |
| $\lambda_{\text{reg}}$ | `0.05` | Weak shrinkage prior; penalizes gratuitous departures from baseline mesh. |

---

## 6. Near-Zero Target Signal Evaluation Policy

In accordance with Phase 1 Revision 1.2.1:
- Numerical signal threshold: $\epsilon_{\text{threshold}} = 10^{-4}\text{ m}$ ($0.1\text{ mm}$).
- When $\bar{\Delta}_{R_{\text{target}}} < \epsilon_{\text{threshold}}$:
  1. `ShapeEvaluationPort` returns `evaluation_status = "insufficient_target_signal"` and `rmsr = None`.
  2. The evaluator assigns the **maximal penalty** $\mathcal{L}_{\text{locality}} = 10.0$.
  3. Under no circumstances is an unavailable RMSR evaluated as $0.0$ or treated as zero leakage.
  4. The candidate step is marked rejected as an uninformative gradient step.
  5. The solver contracts step size (backtracking line search) or prunes the update direction.

---

## 7. Candidate Acceptance & Rejection Criteria

A candidate shape $\mathbf{s}^{(i)}$ at solver iteration $i$ is **strictly rejected** if any of the following conditions hold:

1. **Bounds Violation:** Any component $s_{R, \alpha}^{(i)}$ exceeds provisional bounds $[\mathbf{b}_{R, \min}, \mathbf{b}_{R, \max}]$. (No silent clamping).
2. **Plausibility Failure:** `is_plausible == False` returned by the geometry evaluator (e.g. self-intersecting faces, degenerate triangles).
3. **Insufficient Signal:** Evaluator returns `insufficient_target_signal`.
4. **Tolerance Exceeded:** Residual on any high-reliability measurement ($w_k = 1.0$) exceeds $3 \sigma_k$.

If rejected, the candidate is discarded, a `SolverCandidateDiagnostic` record is generated, and the optimizer contracts its search radius.

---

## 8. Convergence & Maximum-Iteration Policy

To guarantee deterministic low latency suitable for real-time fitting requests:
- **Optimization Algorithm:** Bound-constrained Quasi-Newton (L-BFGS-B or SLSQP) operating on $\mathbf{s} \in \mathbb{R}^{3K}$ within box bounds.
- **Maximum Iterations ($N_{\max}$):** $25$ steps.
- **Relative Objective Tolerance ($\epsilon_{\text{obj}}$):** $\frac{|\mathcal{J}^{(i)} - \mathcal{J}^{(i-1)}|}{\mathcal{J}^{(i-1)}} < 10^{-4}$.
- **Parameter Step Norm ($\epsilon_{\text{step}}$):** $\|\mathbf{s}^{(i)} - \mathbf{s}^{(i-1)}\|_2 < 10^{-3}$.
- **Timeout Limit:** $500\text{ ms}$ wall-clock limit. If timeout occurs, return the best admissible candidate iterate evaluated so far with diagnostic status `"suboptimal_converged"`.

---

## 9. Conclusion & Next Steps

This mathematical proposal maintains complete engine independence. It awaits formal review and sign-off by ChatGPT before activation in the iterative optimizer in Phase 4.
