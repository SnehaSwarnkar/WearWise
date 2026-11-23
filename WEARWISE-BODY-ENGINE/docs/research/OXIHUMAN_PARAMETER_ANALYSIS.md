# OxiHuman Real Capability & Licensing Reconciled Analysis

**Candidate:** OxiHuman (COOLJAPAN OU / Team KitaSan)  
**Evaluation Mode:** Live Crates.io API Inspection, Upstream Manifest Trace, Morph Target Inventory  
**Experiment Date:** 2026-11-23  
**Status:** 🧪 Actual Experiment Result / ✅ Verified Source Fact  

---

## 1. Executive Summary & Licensing Reconciliation

OxiHuman is an independent Rust/WebAssembly human body engine designed to compile MakeHuman-compatible `.target` assets into client-side WebGL/WebGPU renderers.

Before Phase 0 closing, we conducted a rigorous reconciliation between the GitHub source repository, crates.io package metadata, and upstream MakeHuman asset provenance:

### A. The Crates.io BUSL-1.1 Record (Confirmed Fact)
Querying the official Crates.io registry API (`https://crates.io/api/v1/crates/oxihuman`) on 2026-11-23 reveals:
- **Latest Version Published:** `0.0.1` on `2026-11-17T06:10:53Z` by publisher `cool-japan` (KitaSan).
- **Declared License:** **`BUSL-1.1`** (Business Source License 1.1).
- **Official Package Description:**  
  `"Transitional release with no code. OxiHuman comes under the Business Source License 1.1 from its next release: https://cooljapan.tech/bsl/oxihuman/"`
- **Official Repository Link in Metadata:** Changed from GitHub to `https://cooljapan.tech/license/oxihuman/`.
- **Yanked Status of Prior Releases:**
  - Version `0.2.1` (originally published under Apache-2.0 on 2026-03-13) was **formally YANKED** on `2026-11-17T05:15:06Z`.
  - Version `0.1.0` (originally published under Apache-2.0 on 2026-03-11) was **formally YANKED** on `2026-11-17T05:14:06Z`.

### B. The GitHub Source Repository Status (Confirmed Fact)
- Direct HTTP requests to `https://github.com/cool-japan/oxihuman` and GitHub API calls to `https://api.github.com/repos/cool-japan/oxihuman` return **`HTTP 404 Not Found`**.
- Pinned Evidence: The public repository has either been made private, renamed, or removed by its maintainers concurrently with the November 17, 2026 licensing transition.

### C. Asset Provenance vs Engine Code (Confirmed Fact)
- **Engine Logic:** Governed by the repository/crates.io license (historically Apache-2.0, now in transition to BUSL-1.1).
- **Bundled Core Pack Assets (`oxihuman-core-v1.ohpk`):** Derived from MakeHuman Community v1.3.0 (commit `1f508f6083b2f823dab15de924b3bde72e08d77c`) and released under **CC0-1.0 Universal (Public Domain)**. The asset geometries themselves are free of copyleft or commercial restrictions.

### D. Explicitly Unresolved Legal Question
- Whether a commercial entity could legally fork and host the historical Apache-2.0 commit prior to the November 17 transition is an **unresolved legal question** that would require formal intellectual property counsel. 
- However, as demonstrated below, **this question is moot for WearWise**, because OxiHuman is disqualified on product engineering grounds regardless of licensing.

---

## 2. Product Disqualification: Severe Regional Control Gaps

Even if OxiHuman's source code were available under a completely unrestricted permissive license, **it cannot meet the core customization requirements of the WearWise Honest Fit platform**.

According to `PROVENANCE.md`, the core pack `oxihuman-core-v1.ohpk` contains a 21,833-vertex mesh and **exactly 38 sparse morph targets**:
- **30 Macro Details:** Blending corners for binary gender (male/female), age (young/old), muscle tiers (min/avg/max), weight tiers (min/avg/max), 4 height bounds, and 3 ethnic presets.
- **8 Girth Targets:** Bust, underbust, waist, and hip increase/decrease pairs.

### Detailed Zone Coverage Audit:

| WearWise Region | OxiHuman Core Pack Support | Gap Severity | Product Impact on Honest Fit |
|---|---|---|---|
| **Shoulders** | ❌ **ZERO TARGETS** | **FATAL GAP** | Cannot adjust biacromial breadth, shoulder slope, or deltoid volume. Impossible to evaluate T-shirt shoulder seam alignment. |
| **Torso / Chest** | Partial (bust girth $\pm$) | Moderate | Scales chest circumference uniformly; cannot model pectoral bulk or distinct breast projection. |
| **Abdomen** | ❌ **ZERO TARGETS** | **FATAL GAP** | Zero belly protrusion or stomach contour morphs. Cannot represent customers with abdominal volume who need waist ease. |
| **Waist** | Partial (waist girth $\pm$) | Low | Adjusts waistline circumference. |
| **Upper Arms** | ❌ **ZERO TARGETS** | **FATAL GAP** | Zero arm morphs; impossible to evaluate T-shirt sleeve opening or bicep fit. |
| **Lower Arms** | ❌ **ZERO TARGETS** | **FATAL GAP** | Zero forearm morphs. |
| **Hips** | Partial (hip girth $\pm$) | Low | Adjusts hip circumference. |
| **Thighs** | ❌ **ZERO TARGETS** | **FATAL GAP** | Zero thigh morphs; unviable for lower-body garment expansion. |
| **Calves** | ❌ **ZERO TARGETS** | **FATAL GAP** | Zero calf morphs. |

---

## 3. Analysis of `fit_to_measurements`

OxiHuman's measurement-fitting algorithm optimizes the weights of the 8 girth targets using a bounded gradient solver to minimize deviation from target values:
- **Synthetic Self-Consistency:** When fitting a target waist of $80\text{ cm}$, the solver achieves a residual of $<0.5\text{ cm}$ against its own mesh vertices.
- **Lack of External Validation:** This residual is an internal mathematical consistency check on synthetic targets. It does **not** validate that the deformed 3D shape accurately represents an actual human body with an $80\text{ cm}$ waist.

---

## 4. Final Disposition on OxiHuman

**OxiHuman is retained as a documented, non-selected alternative.** 

**Reason for Rejection:**
1. **Product Capability Deficit:** The shipped 38-target core pack lacks independent shoulder, arm, abdomen, thigh, and calf editing. WearWise requires fine-grained regional editing for clothing fit intelligence.
2. **Operational & Licensing Volatility:** The repository is 404/inaccessible, crates.io releases are yanked, and the project is actively transitioning to BUSL-1.1.
