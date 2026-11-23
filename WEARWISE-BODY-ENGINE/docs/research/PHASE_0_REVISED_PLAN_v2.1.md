# WearWise Phase 0: Body Model Feasibility — REVISED Implementation Plan

**Revision:** 2.1 — Final approved plan with technical owner directives incorporated  
**Status:** Approved for immediate execution

---

## Goal

Execute a rigorous, reproducible feasibility study comparing **Anny** (NAVER, Python/PyTorch) and **OxiHuman** (COOLJAPAN, Rust/WASM) as the parametric body-model foundation for WearWise. Deliver a research report with real experimental evidence so that ChatGPT / the technical decision owner can make an evidence-based model selection.

> [!IMPORTANT]
> This is a **technical gate**, not production implementation. No architecture freeze, no backend construction, no frontend changes. All work is strictly isolated inside `WEARWISE-BODY-ENGINE/`.
> Commercial licensing eligibility is a **mandatory production-selection gate**, not merely a weighted comparison criterion. Any candidate failing the legal/licensing gate is disqualified from production adoption.

---

## Verified Machine Environment

| Item | Actual Value |
|---|---|
| OS | Windows 11 (NT 10.0.26300.0), x64 |
| CPU | AMD Ryzen 7 6800H, 8 cores / 16 threads |
| RAM | 15.19 GB |
| GPU | NVIDIA GeForce RTX 3050 Laptop, **4096 MiB VRAM** |
| NVIDIA Driver | 610.88 |
| CUDA UMD | 13.3 (reported by nvidia-smi) |
| CUDA Toolkit (`nvcc`) | **Not installed** (not needed for PyTorch binary wheels) |
| Free Disk | ~99.6 GB |
| Python | 3.12.10 (system) |
| PyTorch | **Not installed** — clean install |
| Rust/Cargo | **Not installed** — installing via rustup with wasm32-unknown-unknown target |
| wasm-pack | **Not installed** — installing for OxiHuman WASM build |
| Node.js | v24.22.1, npm 11.19.1 |
| Existing venvs | None detected |
| Workspace | `WEARWISE-BODY-ENGINE/` isolated workspace |

---

## Technical Directives Incorporated (Revision 2.1)

1. **PyTorch Alone Initially**: Install `torch` alone without `torchvision` or `torchaudio` unless explicitly required by Anny's package dependencies.
2. **Pinned Anny & Native Topology Only**: Target verified official release `anny==0.6.2` (or verified official git tag/commit). Strictly enforce native Anny topology and completely exclude SMPL, SMPL-X, SMPL-H assets, topologies, and optional restricted dependencies.
3. **Controlled Local-Change Sweeps**: Begin local-change sweeps with moderate values `[-0.5, 0.0, +0.5]`. Extreme values `[-1.0, +1.0]` are tested only after moderate geometry passes validity checks.
4. **Documented Neutral Measurement Pose**: Establish and document the exact neutral reference pose (e.g. identity rotation matrices), and enforce identical pose conventions across all measurement experiments.
5. **Rigorous Coordinate Scale Determination**: Determine coordinate scale and units using documented model conventions and controlled height parameter evaluations (e.g., verifying bounding box delta across height parameters), never assuming an arbitrary 1.7m baseline.
6. **Official OxiHuman Native & WASM Build**: Follow official OxiHuman build instructions, including installing the `wasm32-unknown-unknown` target via rustup and `wasm-pack`.
7. **Commercial Licensing as Mandatory Gate**: A candidate failing commercial licensing/provenance criteria is disqualified regardless of technical capabilities.

---

## Experiment Blocks

### Experiment 0 — Environment Setup & Dependency Installation
- Create isolated virtual environment `.venv-anny/`.
- Attempt installing PyTorch CUDA wheel (`torch` alone) targeting cu130, falling back to cu126, then CPU if necessary. Verify with real GPU tensor operation.
- Install pinned `anny==0.6.2` and audit requirements. Install `trimesh`, `pygltflib`, `numpy`, `psutil`.
- Install Rust toolchain via rustup, add target `wasm32-unknown-unknown`, install `wasm-pack`.
- Clone `cool-japan/oxihuman` in an isolated directory and pin commit hash.
- Programmatically log full environment inventory to `experiments/outputs/exp0_environment.json`.

### Experiment A — Anny Real Inference
- Initialize `anny.Anny(local_changes="default")` with native topology.
- Log initialization time, exact version, package metadata, all phenotype and local-change labels.
- Generate documented neutral reference meshes for both male (`gender=1.0`) and female (`gender=0.0`) morphologies.
- Generate at least 5 distinct body variations across the parameter space.
- Export to OBJ and GLB; re-import with independent validators (`trimesh`, `pygltflib`) to verify geometric equivalence, bounds, and normal consistency.
- Save outputs to `artifacts/meshes/`, `artifacts/glb/`, and `experiments/outputs/`.

### Experiment B — Anny Parameter Behaviour Matrix
- Baseline: neutral pose, documented morphology parameters, all local changes at 0.0.
- Determine coordinate axes (which axis is vertical and forward) directly from mesh geometry.
- Controlled sweeps:
  - Phenotype: `[0.0, 0.25, 0.5, 0.75, 1.0]`
  - Local changes: `[-0.5, 0.0, +0.5]` first; only proceed to `[-1.0, +1.0]` if moderate geometry is valid.
- Test required regions: shoulders, torso/chest, abdomen, waist, upper arms, lower arms, hips, thighs, calves, plus L/R symmetry/independence.
- Calculate per-vertex displacement vectors, target-region displacement, and quantify spillover into unrelated regions.
- Build parameter-behaviour matrix in `docs/research/ANNY_PARAMETER_ANALYSIS.md`.

### Experiment C — Anny Anthropometry
- Evaluate native `anny.Anthropometry` module.
- Identify native vs missing measurements for T-shirt fit (chest, waist, hips, shoulder breadth, body length, arm girth/length).
- Establish exact anatomical landmark/cross-section definitions and unit conversions.
- Verify determinism (10 repeated runs) and parameter sensitivity.
- Report limitations and gaps in `docs/research/ANTHROPOMETRY_ANALYSIS.md`.

### Experiment D — OxiHuman Real Capability
- Clone repository and pin exact commit hash. Reconcile release/tag status.
- Build native release with `cargo build --release` and run `cargo test`.
- Build WASM package with `wasm-pack build --target web`.
- Enumerate 38 morph targets from `oxihuman-core-v1.ohpk`. Verify mapping to WearWise regions and record gaps (shoulders, arms, abdomen, thighs, calves).
- Test `fit_to_measurements` on generated mesh; document internal residuals as self-consistency.
- Export GLB and independently validate.
- Document morphology coverage (male/female adult constraints).
- Record findings in `docs/research/OXIHUMAN_PARAMETER_ANALYSIS.md`.

### Experiment E — Hardware Benchmarks
- Benchmark Anny on CPU and GPU (if CUDA available): cold start, first inference, 50 warm inferences (mean/p50/p95), 100-run stability, RAM, peak VRAM, export times, GLB sizes.
- Benchmark OxiHuman: build time, engine startup, mesh generation latency, fit latency, GLB export time, file size, browser/WASM performance.
- Record findings in `docs/research/HARDWARE_BENCHMARKS.md`.

### Experiment F — Licensing and Provenance Audit
- Audit Anny code (Apache-2.0), MakeHuman-derived CC0 mesh/blendshapes, dependencies via `pip-licenses`. Verify total absence of SMPL/SMPL-X.
- Audit OxiHuman code (Apache-2.0), `oxihuman-core-v1.ohpk` CC0 provenance against MakeHuman v1.3.0 upstream commit `1f508f6083b2f823dab15de924b3bde72e08d77c`, Cargo dependencies.
- Compile compliance table with PASS / FAIL / UNRESOLVED commercial readiness gates in `docs/research/LICENSE_AUDIT.md`.

### Deliverables & Report Assembly
- `PHASE_0_RESEARCH_REPORT.md` answering all 10 technical questions.
- `MODEL_COMPARISON.md` with weighted scorecard and licensing gate.
- `RISKS_AND_LIMITATIONS.md`.
- Automated test suite in `tests/`.
- Full README and artifact bundles.
