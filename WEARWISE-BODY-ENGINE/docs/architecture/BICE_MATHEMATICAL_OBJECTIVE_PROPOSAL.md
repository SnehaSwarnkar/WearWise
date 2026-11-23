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

#### Candidate Anthropometric Measurement Acquisition & Interface Contract
**Critical Architectural Boundary:** The existing geometric evaluation port (`ShapeEvaluationPort`) returns **mean vertex displacement magnitudes in meters ($\bar{\Delta}_R$)**. It does **NOT** compute or return physical anthropometric tape circumferences or linear segment lengths ($\hat{m}_k$). Geometric mesh displacement cannot and must not be conflated with anthropometric measurement residuals.

To obtain candidate physical dimensions $\hat{m}_k(\mathbf{s})$ in centimeters during iterative optimization without coupling BICE to 3D geometry processing, we propose a dedicated domain evaluation port: **`AnthropometryEvaluationPort`**.

```python
from typing import Protocol, List, Dict
from app.domain.entities.avatar import AvatarShapeSpec

class AnthropometryEvaluationPort(Protocol):
    """
    Abstract domain port for extracting physical anthropometric measurements
    from a candidate AvatarShapeSpec.
    
    Architecture Relationship:
    - Injected into BICE solver alongside ShapeEvaluationPort.
    - Implemented in Phase 4 by AnthropometryEngine (which performs exact 
      triangle-plane slicing, landmark loop perimeter calculation, and 
      linear caliper extraction).
    - Status: Proposed design contract only; NOT implemented in Phase 3.
    """
    def extract_candidate_measurements(
        self,
        shape_spec: AvatarShapeSpec,
        measurement_codes: List[str]
    ) -> Dict[str, float]:
        """
        Computes physical dimensions in CENTIMETERS for the requested canonical codes.
        """
        ...
```

#### Mathematical Residual Formulation
Let $\mathcal{M}$ denote the set of active physical measurements provided for the body profile. For each measurement $k \in \mathcal{M}$:
- $m_k^*$: Target physical dimension in **centimeters ($cm$)**.
- $\hat{m}_k(\mathbf{s})$: Candidate physical dimension extracted in **centimeters ($cm$)** via `AnthropometryEvaluationPort`.
- $\sigma_k$: Measurement uncertainty tolerance in **centimeters ($cm$)** (`tolerance_cm`, $\sigma_k \ge 0.1\text{ cm}$).
- $w_k$: Reliability policy weight ($w_k \in [0.0, 1.0]$, default $1.00$).

The measurement loss is defined as a normalized, dimensionless squared residual:

$$\mathcal{L}_{\text{meas}}(\mathbf{s}; \mathbf{m}^*) = \begin{cases} 
\frac{1}{|\mathcal{M}|} \sum_{k \in \mathcal{M}} w_k \cdot \left( \frac{\hat{m}_k(\mathbf{s}) - m_k^*}{\sigma_k} \right)^2 & \text{if } |\mathcal{M}| > 0 \\
0.0 & \text{if } |\mathcal{M}| = 0
\end{cases}$$

**Justification & Tolerances Rationale:**
- In the dimensionless squared residual, the effective weight on measurement $k$ is $w_k / \sigma_k^2$. Consequently, dividing the residual by tolerance $\sigma_k$ ensures that measurements captured with high precision (e.g. professional tailor tape with $\sigma = \pm 0.5\text{ cm}$) exert a **16-fold higher squared-residual weight** than loose self-estimates (e.g. user-reported with $\sigma = \pm 2.0\text{ cm}$), since $(2.0 / 0.5)^2 = 16.0$.
- Measurement codes strictly follow canonical definitions: `stature`, `chest_circumference`, `waist_circumference`, `hip_circumference`, `shoulder_breadth`, etc. (all in $cm$).
- **Empty Measurement Set ($\mathcal{M} = \emptyset$):** If no physical measurements are provided for the profile (pure visual styling session), $\mathcal{L}_{\text{meas}} = 0.0$. In this scenario, the solver is driven entirely by visual semantic control preservation and prior regularization ($\mathbf{s} \to \mathbf{s}^{\text{init}}$).
- **Extraction Signal Failure vs Empty Set:** If physical measurements are requested ($|\mathcal{M}| > 0$) but `AnthropometryEvaluationPort` is unavailable or measurement extraction fails for a candidate, $\mathcal{L}_{\text{meas}}$ cannot be computed. Under such failure conditions, the solver records status `measurement_signal_unavailable`, assigns maximal penalty $\mathcal{L}_{\text{meas}} = 10.0$, and rejects the candidate update step.

#### Uncertainty & Reliability Assignment Policy

The values of tolerance $\sigma_k$ and reliability weight $w_k$ are assigned deterministically according to the measurement's acquisition method and validation state:

| Acquisition Method | Validation State | Default $\sigma_k$ (cm) | Reliability Weight $w_k$ | Description / Rationale |
|---|---|---|---|---|
| `PROFESSIONAL_SCAN` | `VERIFIED` | $0.25$ | $1.00$ | Millimeter-accurate 3D hardware scan; highest confidence. |
| `TAILOR_TAPE` | `VERIFIED` | $0.50$ | $1.00$ | Verified manual physical tailoring tape measurement. |
| `TAILOR_TAPE` | `PLAUSIBLE_UNVERIFIED` | $1.00$ | $0.90$ | Manual tape measurement entered without third-party verification. |
| `USER_SELF_REPORT` | `VERIFIED` | $1.50$ | $0.80$ | Self-measured by consumer using guided instructions. |
| `USER_SELF_REPORT` | `PLAUSIBLE_UNVERIFIED` | $2.00$ | $0.70$ | Approximate consumer self-estimate within anatomical bounds. |
| `ESTIMATED_AI` | `PLAUSIBLE_UNVERIFIED` | $2.50$ | $0.50$ | Computer-vision or statistically inferred dimension. |
| *Any Method* | `OUTLIER_FLAGGED` | $5.00$ | $0.10$ | Flagged as anthropometrically suspect; heavily downweighted. |

*(Note: All tolerances and weights in this table represent provisional engineering baselines, subject to empirical calibration during Phase 4 integration).*

### 4.2 Semantic Control Preservation Loss ($\mathcal{L}_{\text{ctrl}}$)

Let $\mathbf{s}^{\text{init}}(\mathbf{c}^*) = \mathcal{M}_{\text{rules}}(\text{normalize}(\mathbf{c}^*))$ be the deterministic regional scales directly projected from consumer sliders $\mathbf{c}^*$ via `map_controls_to_regional_scales`.

The semantic preservation loss penalizes deviations from the shopper's explicit visual preference:

$$\mathcal{L}_{\text{ctrl}}(\mathbf{s}; \mathbf{c}^*) = \frac{1}{|\mathcal{C}|} \sum_{j \in \mathcal{C}} \left( s_j - s_j^{\text{init}}(\mathbf{c}^*) \right)^2$$

Where $\mathcal{C}$ indexes the active mapped regional scale axes.

**Justification:** Quadratic penalty ensures that the solver minimally modifies user-adjusted sliders only to the extent necessary to satisfy hard anthropometric circumferences.

### 4.3 Geometric Locality Penalty ($\mathcal{L}_{\text{locality}}$)

Locality is evaluated via `ShapeEvaluationPort`. In a general deformation scenario where a subset of regions $\mathcal{R}_{\text{target}} \subseteq \mathcal{R}$ are intentionally modulated:

For each non-target region $R \in \mathcal{R} \setminus \mathcal{R}_{\text{target}}$, the relative mean surface displacement ratio (RMSR) is evaluated against the peak target displacement:

$$\text{RMSR}_R(\mathbf{s}) = \frac{\bar{\Delta}_R(\mathbf{s})}{\max_{T \in \mathcal{R}_{\text{target}}} \bar{\Delta}_T(\mathbf{s})}$$

The locality loss aggregates the maximal spillover across all un-targeted anatomical zones:

$$\mathcal{L}_{\text{locality}}(\mathbf{s}) = \begin{cases}
\max_{R \in \mathcal{R} \setminus \mathcal{R}_{\text{target}}} \text{RMSR}_R(\mathbf{s}) & \text{if } \mathcal{R} \setminus \mathcal{R}_{\text{target}} \ne \emptyset \text{ and } \mathcal{R}_{\text{target}} \ne \emptyset \\
0.0 & \text{if } \mathcal{R}_{\text{target}} = \mathcal{R} \text{ (all regions modulated)} \\
0.0 & \text{if } \mathcal{R}_{\text{target}} = \emptyset \text{ (no intentional deformation)}
\end{cases}$$

When evaluating single-region test impulses ($|\mathcal{R}_{\text{target}}| = 1$), this reduces to the canonical Phase 1 Revision 1.2.1 formula: $\text{RMSR}_R(\mathbf{s}) = \bar{\Delta}_R(\mathbf{s}) / \bar{\Delta}_{R_{\text{target}}}(\mathbf{s})$.

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

> [!NOTE]
> All loss weights ($\lambda_{\text{meas}}, \lambda_{\text{ctrl}}, \lambda_{\text{loc}}, \lambda_{\text{reg}}$), tolerances ($\sigma_k$), and penalty values are **provisional engineering baselines**. They are explicitly isolated in configuration structures to permit empirical tuning during Phase 4 physical avatar calibration.

---

## 6. Near-Zero Target Signal Evaluation Policy

In accordance with Phase 1 Revision 1.2.1:
- Numerical signal threshold: $\epsilon_{\text{threshold}} = 10^{-4}\text{ m}$ ($0.1\text{ mm}$).
- When $\max_{T \in \mathcal{R}_{\text{target}}} \bar{\Delta}_T < \epsilon_{\text{threshold}}$:
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

## 8. Optimization Algorithm, Gradient Strategy & Termination Policy

To guarantee deterministic low latency suitable for real-time fitting requests:

### 8.1 Algorithm & Gradient Approximation
- **Optimization Algorithm:** Bound-constrained Limited-memory Broyden–Fletcher–Goldfarb–Shanno with Box constraints (**L-BFGS-B**), operating on regional parameter vector $\mathbf{s} \in \mathbb{R}^{3K}$ constrained strictly within $[\mathbf{b}_{\min}, \mathbf{b}_{\max}]$.
- **Gradient Strategy:** Because the `AnthropometryEvaluationPort` and `ShapeEvaluationPort` rely on 3D mesh surface extraction and slicing, analytical derivatives $\nabla_{\mathbf{s}} \mathcal{J}(\mathbf{s})$ are unavailable in closed form. Gradients are computed numerically using **central finite differences**:
  $$\frac{\partial \mathcal{J}}{\partial s_j} \approx \frac{\mathcal{J}(\mathbf{s} + h \mathbf{e}_j) - \mathcal{J}(\mathbf{s} - h \mathbf{e}_j)}{2h}$$
  with perturbation step $h = 10^{-4}$.

### 8.2 Convergence & Termination Policy
- **Maximum Iterations ($N_{\max}$):** $25$ steps.
- **Zero-Safe Relative Objective Convergence ($\epsilon_{\text{obj}}$):**
  $$\Delta_{\text{rel}} = \frac{|\mathcal{J}^{(i)} - \mathcal{J}^{(i-1)}|}{\max(|\mathcal{J}^{(i-1)}|, 10^{-9})} < 10^{-4}$$
- **Parameter Step Norm ($\epsilon_{\text{step}}$):** $\|\mathbf{s}^{(i)} - \mathbf{s}^{(i-1)}\|_2 < 10^{-3}$.
- **Wall-Clock Timeout Limit:** $500\text{ ms}$ hard limit.
- **Diagnostic Status Distinction:**
  - If $\Delta_{\text{rel}} < 10^{-4}$ or $\|\Delta \mathbf{s}\|_2 < 10^{-3}$: Returns status `"converged"`.
  - If the $500\text{ ms}$ wall-clock budget expires before convergence: Returns status `"timeout_suboptimal"`.
  - If $N_{\max} = 25$ is reached without meeting tolerance: Returns status `"iteration_limit_exceeded"`.
  *(Under no circumstances is a timed-out or iteration-truncated solve reported as `"suboptimal_converged"` or masked as an optimal solution).*

---

## 9. Conclusion & Next Steps

This mathematical proposal maintains complete engine independence. It awaits formal review and sign-off by ChatGPT before activation in the iterative optimizer in Phase 4.
