# WEARWISE — Master Product, Research & Engineering Brief

**Version:** 1.0  
**Date:** 23 November 2026  
**Status:** Product direction consolidated; model foundation remains subject to Phase 0 experiments  
**Primary working principle:** ChatGPT owns product and technical decisions; Antigravity implements only explicitly assigned work; the project owner reviews the outputs and provides user feedback.

---

## 0. How to use this document

This document consolidates the 108-page *Project Planning Review.pdf* and the earlier *WearWise_Master_Project_Concept.pdf*, while adding current technical research checks. It is the working baseline for future decisions and Antigravity tasks.

Decision labels used throughout:

- **APPROVED** — explicitly confirmed in the recovered conversation.
- **DIRECTION** — strong architectural/product direction supported by the recovered conversation; retain unless evidence disproves it.
- **PROVISIONAL** — current recommendation, but it must pass a technical, licensing or validation gate.
- **RESEARCH PENDING** — cannot be responsibly decided without an experiment or more evidence.
- **FUTURE** — part of the long-term product vision, not a current implementation requirement.

Where the source documents disagree, the newer Honest Fit direction takes precedence for engineering priorities. The original fashion-assistant vision is retained as the larger product experience; it is not discarded.

## 1. Executive product definition

**WearWise is an AI-powered personal fashion assistant and shopping platform whose technical differentiator is honest, explainable garment-fit intelligence.**

WearWise must help a customer answer three distinct questions:

1. **Visual:** What might this garment look like on my body representation?
2. **Compatibility:** How do my body measurements compare with the seller's actual garment measurements, zone by zone?
3. **Decision:** Which available size is the best option, what trade-offs does it have, and why?

These are separate engineering problems. A visually convincing try-on image must never be treated as evidence that a garment physically fits. A numeric fit result must not be confused with a physically simulated cloth deformation.

The central product loop remains:

**DISCOVER → UNDERSTAND → VISUALIZE → COMPARE → STYLE → DECIDE → LEARN**

Product philosophy: **useful first, engaging second, shopping third.** A visitor must be able to browse without first submitting a photograph, body type, budget or measurements. Personalization should be optional and progressively unlocked.

### Core differentiation

Most shopping interfaces make customers infer fit from a model, size label or generic size chart. WearWise combines:

- a user-controlled parametric body representation;
- body measurements with explicit provenance and uncertainty;
- actual per-size garment dimensions supplied by the seller;
- fabric and fit-intention information;
- deterministic, explainable, body-zone fit calculations; and
- a visual representation of the calculated fit zones.

The platform should not claim perfect fit or objective attractiveness. It is a decision-support system whose accuracy must be measured and communicated honestly.

## 2. Approved product decision register

The following decisions are treated as the approved product baseline recovered from the prior conversation.

| ID | Decision | Status |
|---|---|---|
| WW-001 | WearWise combines AI fashion assistance, e-commerce and an honest-fit experience. | APPROVED |
| WW-002 | Long-term market is international. | APPROVED |
| WW-003 | Audiences include consumers, sellers and retailers. | APPROVED |
| WW-004 | No mandatory photographs, camera scans or body scans. | APPROVED |
| WW-005 | Users create body representations from their inputs, measurements and visual customization. | APPROVED |
| WW-006 | Avatar appearance is a proportionally accurate, realistic human with a neutral mannequin appearance. It is not a photorealistic face-first avatar or a stylized game character. | APPROVED |
| WW-007 | Body editing starts with four primary groups and supports finer regional adjustments. | APPROVED |
| WW-008 | Support male and female anatomical morphologies in the product's body-model layer. | APPROVED |
| WW-009 | Tape measurements are optional; unknown measurements may be estimated. | APPROVED |
| WW-010 | The source and uncertainty of every body measurement must be communicated. | APPROVED |
| WW-011 | T-shirts are the first garment category; the data model must be extensible. | APPROVED |
| WW-012 | Sellers provide actual garment dimensions and fabric information for every size variant. | APPROVED |
| WW-013 | Assisted extraction from uploaded size charts is a later feature. | APPROVED |
| WW-014 | Initial global fit preferences: slim, regular, relaxed and oversized. | APPROVED |
| WW-015 | Recommendations include regional fit explanations. | APPROVED |
| WW-016 | WearWise must not falsely recommend a size when no offered size is suitably compatible. | APPROVED |
| WW-017 | The avatar is rotatable and can display measurements and fit zones. | APPROVED |
| WW-018 | Full garment visualization is a long-term objective. | APPROVED |
| WW-019 | Build a separate body/core backend and connect it to the existing app through APIs. | APPROVED |
| WW-020 | Commercially compatible dependencies and assets are mandatory from the beginning. | APPROVED |
| WW-021 | Initial infrastructure budget is ₹0; use local hardware first. | APPROVED |
| WW-022 | Preserve the existing React + Vite frontend. Do not rebuild or redesign it. | APPROVED |
| WW-023 | English initially. | APPROVED |
| WW-024 | Defer monetization decisions until the product works. | APPROVED |
| WW-025 | First prototype prioritizes actual model inference and clearly disclosed limitations. | APPROVED |
| WW-026 | One overall fit preference initially; regional preference controls can follow. | APPROVED |
| WW-027 | Show a closest alternative with a clear warning where useful, but explicitly mark the result as no suitable size. | APPROVED DIRECTION |
| WW-028 | Basic fabric-stretch handling first; design the schema so directional stretch and recovery can be added. | APPROVED DIRECTION |

### Additional product interpretation

- The editor should feel like a useful character creator: select a body region, adjust it with a slider, and immediately see the geometry respond.
- Provide quick presets/default body shapes for users who do not know their measurements, while retaining a custom path for better personalization.
- The initial four groups are **upper body, torso, arms and lower body**. Within these, provide region-level controls such as shoulders, chest/torso, abdomen, upper/lower arms, hips, thighs and calves as the selected model actually supports them.
- Do not imply that height and weight determine a person's exact chest, shoulder, hip or limb dimensions. The inverse problem is underdetermined.
- A body-shape label is descriptive, not a judgement. No body type should be presented as better or worse.
- Do not expose ethnicity/race-coded body parameters as user-facing sliders. They are not appropriate identity controls and can encode stereotypes.
- Initially treat the product as adult-focused unless a separately validated, appropriately licensed model and child-safety/privacy design justify a broader age range.

## 3. Product scope and prioritization

### Priority 1 — Honest Fit core

1. Free product discovery and T-shirt catalogue integration.
2. Preset and custom body avatar creation.
3. Body Intelligence & Calibration Engine (BICE).
4. Anthropometric measurement extraction and provenance.
5. Seller-side product and per-size measurement system.
6. Fabric composition/construction and basic stretch metadata.
7. Deterministic per-zone fit engine.
8. Size ranking, alternatives and explainable fit verdict.
9. Rotatable avatar with body measurements and fit-zone overlays.
10. API contracts and independent backend verification.

### Priority 2 — Broader fashion intelligence

- Personal colour advisor (optional questionnaire/manual correction first; image analysis only as an experimental and controlled feature).
- Compare My Sizes and Compare My Looks.
- User feedback after purchase/wearing.
- Better style profile and recommendation explanations.
- Seller tooling and catalogue quality workflows.

### Priority 3 — Long-term extensions

- My Wardrobe and smart-purchase guidance.
- Style DNA, Complete My Look, occasion styling and What If exploration.
- Advanced personalization and feedback learning.
- Assisted size-chart extraction.
- Full garment geometry, SIZER/TailorNet-inspired deformation, physics-based cloth simulation and AR.
- Sarees and complex garment categories after the T-shirt pipeline is validated.

**Important:** The original WearWise experience—free browsing, Style DNA, colour guidance, Compare My Looks, Complete My Look, occasion styling, My Wardrobe and progressive personalization—remains the long-term product. The newer Honest Fit direction changes the immediate engineering priority; it does not delete the wider vision. Existing frontend pages and features should be preserved. Their exact implementation status has not yet been code-audited.

### Explicitly not in the first core release

- Diffusion/image-generation virtual try-on as a proxy for fit.
- Full physical cloth simulation.
- AR try-on.
- A general-purpose fashion chatbot as the main innovation.
- A neural network or LLM deciding whether a size fits.
- A new body model trained from scratch without evidence and approval.

## 4. Product experience and flagship demonstration

### Progressive user journey

1. Visitor enters and browses the catalogue without compulsory onboarding.
2. Visitor opens Build Avatar when they want fit assistance.
3. They choose a preset or create a custom neutral mannequin avatar.
4. They enter height and weight; any known tape measurements are optional.
5. The interface lets them make broad adjustments and then refine selected body regions.
6. WearWise produces a 3D mesh and a body profile. Measurements are clearly tagged as user-reported, model-estimated or geometry-extracted.
7. User selects a T-shirt.
8. WearWise retrieves actual seller measurements for each available size and the fabric/fit metadata.
9. The fit engine evaluates each size by body zone and fit preference.
10. The user sees a recommendation, alternatives, region-level fit states and an explanation.
11. Where no size is suitable, the interface says so and identifies the closest alternative with a warning.
12. User can save the decision and optionally submit post-purchase fit feedback.

### Recommended first demonstration

Use one coherent scenario: a customer wants an olive T-shirt, builds or selects an avatar, compares sizes M/L/XL, sees how chest, shoulders and length behave, and receives a size recommendation with a numerical explanation and limitations. This demonstrates the actual engineering contribution better than eight disconnected AI demos.

## 5. System architecture

### Repository strategy

**Repository A — Existing WearWise frontend**

- Existing React 19 + Vite application.
- Existing page and component structure must be preserved.
- Reported pages include BuildAvatar, TryOn, StyleAnalysis, Wardrobe, Assistant and Cart; this is based on the conversation, not a repository audit.
- Existing Three.js / React Three Fiber viewer should be reused if it can load the required mesh assets.

**Repository B — WEARWISE-CORE (planned production backend)**

- A modular FastAPI application.
- PostgreSQL for structured users, body profiles, sellers, products, variants, measurements, fit preferences and feedback.
- Model-specific code behind an adapter interface.
- Independent BICE, anthropometry and deterministic fit modules.
- GLB assets served through controlled API access or an object-storage abstraction later.
- No premature microservice split. Module boundaries first; deployment separation only if measured requirements justify it.

**Temporary Phase 0 workspace — WEARWISE-BODY-ENGINE**

The latest recovered instruction names `WEARWISE-BODY-ENGINE` for isolated avatar-model feasibility experiments. Treat this as a temporary research/POC workspace, not an additional permanent production microservice. After the model decision, selected, licensed code and adapter work can be moved into the appropriate `WEARWISE-CORE` module.

### High-level component layout

```text
Existing React + Vite application
  ├── BuildAvatar UI ───────────────┐
  ├── Honest Fit / TryOn UI ────────┤
  ├── Catalogue / Seller UI ────────┤ REST + GLB
  └── Existing 3D viewer ──────────┘
                                      │
WEARWISE-CORE (FastAPI modular monolith)
  ├── API / auth / validation
  ├── Body Intelligence & Calibration (BICE)
  ├── Avatar Engine adapter (candidate model)
  ├── Anthropometry
  ├── Body Profile / Asset repository
  ├── Seller / Product / Size Variant catalog
  ├── Garment Measurement protocol
  ├── Honest Fit Engine
  ├── Fit Report / Explanation
  └── PostgreSQL + migrations
```

### Core data flow

```text
User inputs + optional tape measurements
        ↓
Input normalization + provenance
        ↓
BICE: initial parameter estimate + constrained calibration
        ↓
Avatar model adapter → real 3D body mesh
        ↓
Anthropometry → standardized body measurements
        ↓
Calibrated Body Profile + uncertainty + model version
        ↓
Seller product + per-size garment dimensions + fabric data
        ↓
Deterministic Honest Fit Engine
        ↓
Per-zone fit assessment + size ranking + warnings
        ↓
REST response + fit-zone metadata + GLB asset
        ↓
Existing frontend visualizes and explains the result
```

### Proposed internal backend layout

```text
WEARWISE-CORE/
  app/
    api/
    core/                 # configuration, logging, errors, security
    modules/
      body_intelligence/
      avatar_engine/
      anthropometry/
      body_profiles/
      seller_catalog/
      garment_measurements/
      fit_engine/
      recommendations/
      feedback/
    schemas/
    repositories/
  migrations/
  tests/
  scripts/
  artifacts/              # generated assets; large/restricted assets excluded from Git
  calibration_data/       # provenance documented; no personal data without consent
  docs/
  PROJECT_MASTER_SPEC.md
  AGENTS.md
  README.md
  .env.example
```

Do not implement this production repository until Phase 0 is reviewed and the architecture has been frozen. The Phase 0 POC must remain small and isolated.

## 6. Avatar foundation and Body Intelligence & Calibration Engine

### What the external model does—and does not do

A parametric model generates a mesh from its own parameters. It does not natively understand WearWise concepts such as “my waist is 92 cm”, “make my abdomen fuller”, or “broaden only my shoulders”. WearWise needs its own translation and calibration layer.

For SMPL-family models, shape is commonly represented by coefficients such as β. Anny has semantic phenotype controls and local shape changes. OxiHuman exposes morph targets and measurement fitting. Neither candidate should be assumed to match a real person merely because a mesh can be generated.

### BICE responsibility

BICE is the WearWise-owned intelligence layer between the UI and the selected body-model backend. It should be model-agnostic.

1. **Input layer:** height, weight, body morphology selection, preset, user-friendly shape sliders and optional tape measurements.
2. **Normalization:** canonical units, ranges, missing-value handling and provenance.
3. **Initialization:** produce a plausible initial set of model parameters from the available profile and semantic controls.
4. **Calibration:** adjust supported parameters to minimize disagreement with user-confirmed measurements while preserving the selected visual/body-shape intent and avoiding implausible geometry.
5. **Validation:** detect impossible targets, parameter conflicts, unsupported morphs and excessive residual error.
6. **Output:** model parameters, generated mesh, extracted measurements, residuals, confidence/uncertainty and version information.
7. **User correction:** allow users to edit measurements and avatar appearance; persist the correction separately from the model's estimate.

### Hybrid calibration, not a one-shot regression

A regression from `(height, weight, waist, sliders) → model parameters` can be used as an initializer or surrogate after a suitable calibration dataset exists. It must not be presented as a guaranteed reconstruction. The problem is underdetermined: people with the same height, weight and waist can have different chest, shoulder, hip and limb proportions.

The later optimizer may use an objective such as:

```text
parameters* = argmin_parameters [
    λm · measurement_error(parameters)
  + λs · semantic_shape_error(parameters)
  + λp · body_prior_error(parameters)
  + λl · locality / spillover penalty(parameters)
]
```

- Measurement error penalizes disagreement with known tape measurements.
- Semantic-shape error preserves the selected qualitative body controls.
- Body prior penalizes implausible shapes outside the supported body model.
- Locality penalty discourages a regional slider from unintentionally changing unrelated regions.

This is a design formulation, not a finished validated optimizer. Choose exact terms and weights only after the candidate model experiments.

### Quick Avatar and Precision Avatar

**Quick Avatar:** height, weight, preset/body-shape selection and broad sliders. It generates a plausible representation, with estimates marked as estimates and lower confidence where appropriate.

**Precision Avatar:** the same editor plus optional user-confirmed tape measurements. These become stronger calibration anchors. This path should materially improve the fit analysis when accurate values are supplied.

Weight is a profile attribute and may inform shape initialization. Do not derive and advertise a person's actual weight by multiplying mesh volume by a universal body-density assumption. Do not treat model-derived BMI as a verified personal measurement.

### Measurement provenance contract

Every measurement must include at least:

- `value`;
- `unit` (canonical internal unit: centimetres for body/garment dimensions; kilograms for weight);
- `source`: `user_reported`, `model_estimated`, `geometry_extracted` or `seller_measured`;
- `method` / measurement definition;
- `confidence` or uncertainty where the method supports it;
- timestamp and model/calibration version where applicable.

A seller-measured garment dimension and a body circumference are not interchangeable. A flat garment width is not a circumference. Preserve measurement conventions in storage and APIs.

## 7. Candidate avatar-model research and current decision

### Current decision: do not freeze the model yet

**Anny is the leading candidate for detailed regional editing. OxiHuman is a mandatory comparison candidate.** Neither is approved as final until its actual outputs, control behaviour, measurement extraction, runtime, asset provenance and licence are tested on the target machine.

The model decision is a gate, not a preference vote.

### Anny — leading candidate, provisional

Current public documentation indicates:

- Official project: https://github.com/naver/anny
- Shape parameterization docs: https://naver.github.io/anny/build/shape_parameterization.html
- Documented release v0.6.2 dated 26 October 2026.
- Python >=3.10 and PyTorch >=2.0 in the package metadata.
- Semantic phenotype parameters and local mesh modifications for body areas such as torso, abdomen, arms, hips, thighs, calves and shoulders.
- An anthropometry module, but the documented quick example is not a complete clothing-measurement solution; it demonstrates only a limited set of outputs (including height and waist), and uses a buoyancy assumption for its BMI estimate.
- Native Anny assets/code are described under Apache-2.0/CC0 terms, but every actual model asset and transitive dependency must be audited. Optional SMPL-X-related content is separately restricted.

**Implementation constraints for the POC:**

- Use Anny's native topology and assets only.
- Do not install/use its SMPL/SMPL-X optional topology or any non-commercial SMPL/SMPL-X model files.
- Do not expose ethnicity/race-coded phenotype parameters in the consumer UI.
- Test each local parameter independently. Its name does not prove it sets an exact centimetre target.
- Test for geometry artefacts and regional spillover; Anny documentation warns that large local changes can become unrealistic.
- Use the official documented installation/inference path; avoid optional dependency groups unless the experiment proves they are necessary.

### OxiHuman — alternative candidate, provisional

Current repository: https://github.com/cool-japan/oxihuman  
Documentation: https://docs.rs/oxihuman/latest/oxihuman/  
Browser playground: https://play.cooljapan.dev/human

The repository documents a Rust/WebAssembly-oriented parametric body engine and reports a compact core pack with morph targets, a body mesh, measurement fitting and GLB export. Its own project files label version 0.2.1 as **unreleased** / awaiting production release approval. Repository-reported geometry counts, test counts, benchmark timings and measurement errors are claims to reproduce, not independent validation.

Important candidate limitations to test:

- Does its current body pack actually support independently useful shoulder, arm, abdomen, hip, thigh and calf adjustments?
- Is the current core mesh a bodysuit-style adult mesh rather than a fully detailed human representation?
- Does it support the morphology coverage WearWise requires?
- Does `fit_to_measurements` solve only a small set of target measures (reported around height, chest/bust, waist and hip), and what are its residual/error characteristics?
- Can its GLB export and browser/WASM integration work with the existing application?
- Are the code, morph targets and all bundled assets commercially distributable and usable?

OxiHuman's self-test against meshes generated by its own pack is not equivalent to validation against external human tape measurements.

### Research-only references—not MVP dependencies

| Research | Contribution to WearWise | Decision |
|---|---|---|
| SMPL | Foundational parametric body representation and shape coefficients | Study; do not use model files in the commercial product under the current free licence |
| SMPL-X | Extended body/hand/face representation | Do not use restricted assets absent a separate commercial licence |
| BodyTalk | Semantic body descriptors and interpretable controls | Use as design methodology; no need to integrate its research model |
| SCAPE | Historical shape/pose decomposition | Related work only |
| SHAPY | Semantic + metric attribute-to-shape estimation and calibration methods | Study methods; code/models/data licensing is research-only unless separately licensed |
| SIZER | Size-sensitive 3D garment geometry and parsing | Future garment-deformation research; does not replace seller dimensions or fit mathematics |
| TailorNet | Pose/shape/style-conditioned garment deformation and wrinkles | Future physical visualization; not a fit engine |
| FIT (2026) | Large fit-aware dataset with garment/body measures and ill-fitting cases | Literature and future benchmark reference; verify dataset terms before any use |

### Model-selection scorecard (after legal gate)

A candidate that fails commercial asset/code licensing is disqualified from production regardless of its technical score.

For candidates that pass the legal gate, score evidence on:

| Criterion | Weight |
|---|---:|
| Anthropometric usefulness and external validation potential | 30% |
| Independent regional control quality and controllability | 20% |
| Mesh/topology quality for the neutral mannequin and garment zones | 15% |
| Runtime, memory and interactive performance on target hardware | 15% |
| Operational maturity, reproducibility and dependency stability | 10% |
| GLB/browser integration quality | 10% |

Do not award points for unverified marketing claims. Each score must cite an experiment, source or unresolved assumption.

## 8. Anthropometry specification

The avatar is for fit assessment, so a pretty mesh with incorrect measurements is a failed foundation.

### First measurement dictionary for T-shirts

**Buyer/body measurements:** height, chest/bust circumference, waist circumference, hip circumference, shoulder breadth, torso length, upper-arm circumference, lower-arm circumference where useful, sleeve/arm length, thigh/calf dimensions for future categories. A measurement should only be returned if the method and landmarks are defined and the mesh supports it.

**Seller/garment measurements:** chest circumference or flat chest width, shoulder seam-to-seam width, body length (with defined start landmark), sleeve length (with defined start landmark), hem width/circumference, optional sleeve-opening width/circumference. For T-shirts, start with a small, high-value required set and make secondary measurements optional where they are not needed for a reliable recommendation.

### Standardization requirements

- Use a single neutral reference pose and orientation for mesh measurements.
- Define anatomical landmarks and cross-section plane orientation.
- Record whether the number is a circumference, full width, half-width, length or distance between landmarks.
- Store canonical units and convert only at clear API/UI boundaries.
- Ensure that mesh scale normalization is known and tested. Do not assume model coordinates are centimetres.
- Measure the same body/garment location consistently across buyer and seller records.
- Repeat each measurement extraction and test its reproducibility.

Anny's built-in anthropometry is a starting point, not the complete WearWise anthropometry engine. Implement additional mesh-based measurement extraction only after confirming landmarks, coordinate scale and neutral pose.

## 9. Seller product and garment measurement system

The seller experience must capture enough reliable data without making product listing so burdensome that sellers abandon it.

### T-shirt minimum data

For every size variant (e.g. S, M, L, XL):

1. Size label (informational only; do not use it as the numerical fit input).
2. Chest measurement, with explicit method (`flat_width` or `circumference`).
3. Shoulder width (seam-to-seam convention).
4. Body length (defined measurement path).
5. Sleeve length (defined measurement path).
6. Unit.

Optional/additional fields:

- Hem width/circumference.
- Sleeve opening.
- Neck/rib dimensions if needed by a garment category.
- Fabric fibre composition.
- Construction: knit/woven and, for T-shirts, knit structure where known.
- Declared fit intention: slim, regular, relaxed or oversized.
- Stretch direction (horizontal/vertical), measured extension and recovery, test method/conditions when available.

### Seller data rules

- Actual dimensions per size take priority over generic brand size charts.
- Product size labels are not standardized across brands; never assume that all M sizes are identical.
- A flat width is not the full circumference. Convert only when the measurement method explicitly supports it; validate seller entry with clear diagrams/instructions.
- Incomplete products may be stored, but fit recommendations must be restricted, marked low confidence or unavailable where critical data is missing. Do not invent missing measurements with AI and present them as seller-measured.
- Keep the required seller form lean. Add advanced fabric testing fields progressively.

## 10. Honest Fit Engine — mathematical design

The fit engine is deterministic Python business logic. It receives normalized data and returns structured results. It does not call an LLM to decide fit.

### Core sequence

1. Validate required buyer measurements and provenance.
2. Validate seller garment measurements, conventions and per-size completeness.
3. Normalize units and measurement definitions.
4. For each relevant zone, calculate **garment ease**:

   `ease_i = garment_measurement_i - body_measurement_i`

5. Determine a **target/ideal ease profile** for garment category, declared fit intention and fit preference.
6. Calculate each zone's deviation from its target ease:

   `deviation_i = ease_i - target_ease_i`

7. Apply zone-specific penalties/weights and critical-zone constraints.
8. Rank available sizes, preserving unacceptable/critical failure states.
9. Return a size recommendation or `NO_SUITABLE_SIZE`, alternatives and a machine-readable explanation.

### Do not use universal arbitrary thresholds

The earlier conversation contained illustrative delta bands (for example, below -8 cm as “will not fit”). Those were explicitly identified as prototype examples, not validated universal standards. Do not hard-code them as universal rules.

A slim T-shirt, regular T-shirt and oversized T-shirt should have different target-ease ranges. The desired ease also differs by body zone and garment construction. A negative ease may be intentional in some stretchy garments and unacceptable in others.

A 2026 multi-dimensional apparel fit study uses target ease, dimensional zones, weighted penalties and Top-K recommendations. Its reported jacket results are not evidence of T-shirt accuracy or global validity. Use its method as a design reference only; calibrate WearWise's own T-shirt targets using real garment trials.

### Ranking and explanation

The API response should contain, for every candidate size:

- calculated ease per zone;
- target ease/range per zone and its source/version;
- zone classification (e.g. tight, within preference, loose, insufficient length);
- zone penalty/weight and aggregate score (if a score is exposed);
- critical warnings and missing data;
- provenance/uncertainty flags;
- reason for ranking ahead of other sizes.

The interface must not imply that a compatibility percentage is an objective truth. It is a model-based score tied to defined assumptions and validation evidence.

### No suitable size handling

Return `NO_SUITABLE_SIZE` when all available sizes breach critical compatibility criteria. If helpful, still show the closest size as an explicitly warned alternative. Never relabel the closest bad option as a good fit merely because it ranks first among poor candidates.

### Fabric stretch: cautious first implementation

Composition alone does not determine comfortable stretch. Construction, knit/weave, stretch direction, extension under load, stretch recovery and garment construction all matter. Do not multiply garment dimensions by an arbitrary factor because the garment contains elastane.

For the first release:

- store composition and construction;
- optionally store a seller-declared basic stretch class;
- only use a numeric stretch adjustment when a defined test method, direction, load/extension and recovery information are available;
- expose assumptions and lower confidence where the fabric data is incomplete.

The schema can later support standard test references such as ASTM D3107 for woven stretch fabrics and ASTM D2594/D2594M for low-power knitted fabrics. Do not claim a seller's values comply with those standards unless the prescribed test was actually performed.

## 11. Fit visualization versus physical garment simulation

These are different capabilities and must remain separate:

1. **Fit calculation:** deterministic numerical comparison of body/garment data.
2. **Fit visualization:** colour-coded regions on the neutral avatar based on the fit engine's structured output (e.g. tight / acceptable / loose / insufficient length). This is achievable without fabric physics.
3. **Physical garment simulation:** garment geometry deforms, stretches, wrinkles and drapes against the body. This requires actual garment patterns/geometry and a suitable learned or physics-based simulation pipeline.

The first release implements levels 1 and 2. It must not depict simulated fabric tension when no simulation exists. Keep the GLB body mesh and per-zone fit metadata as separate API resources.

## 12. Data and API design direction

These are architecture proposals to be frozen after Phase 0; they are not final database migrations.

### Main domain entities

- `User` / `Account`
- `BodyProfile`
- `BodyMeasurement` (value, unit, source, method, confidence, timestamp)
- `AvatarAsset` (asset location, format, model version, parameters/calibration version)
- `Seller`
- `Product`
- `ProductVariant` / `SizeVariant`
- `GarmentMeasurement` (value, unit, measurement type, measurement convention, method)
- `FabricProfile`
- `FitPreference`
- `FitEvaluation`
- `FitZoneResult`
- `FitFeedback`

### API areas (illustrative names; final contracts come after architecture freeze)

- `/api/v1/body-profiles`
- `/api/v1/body-profiles/{id}/avatar` (generate/update preview or committed avatar)
- `/api/v1/body-profiles/{id}/measurements`
- `/api/v1/avatar-assets/{asset_id}` (GLB retrieval, authorization checked)
- `/api/v1/sellers`
- `/api/v1/products`
- `/api/v1/products/{id}/variants`
- `/api/v1/products/{id}/fit-evaluations`
- `/api/v1/fit-evaluations/{id}`
- `/api/v1/fit-feedback`

Use versioned Pydantic request/response schemas, explicit errors, input validation, pagination where appropriate, and an API collection or executable examples for handoff. The frontend should never import internal Python modules.

### Preview performance

- Load the selected model once per worker/process; do not reload it for every slider action.
- Debounce slider requests (initial design target around 250–400 ms; benchmark and tune).
- Cache identical parameter sets when safe.
- For repeated previews, investigate sending updated vertex buffers while preserving mesh topology rather than retransmitting the entire mesh each time.
- Keep a stable topology and asset contract for the frontend viewer.
- Benchmark before introducing queues, GPU servers or microservices.

## 13. Persistence, privacy and security

- PostgreSQL is the preferred production data store for structured buyer/seller/product/measurement records.
- Use JSON fixtures/local test data for early isolated experiments only; do not treat them as the final structured data model.
- Body profiles are sensitive personal data. Store only necessary fields, restrict access by user ownership and protect transport/storage.
- Sellers must not see individual buyer measurements.
- A user must be able to delete saved body profiles and generated avatar assets.
- Do not require or collect a photograph for the core avatar/fit pipeline.
- Restrict access to GLB/body assets; use expiring/authorized access where applicable.
- Never commit pretrained weights/model assets that are restricted, credentials, secrets or real user measurement data to Git.
- Record model, model asset, calibration and measurement-protocol versions with generated body profiles and fit reports.
- Maintain dependency, asset provenance and licence records.

## 14. Validation and acceptance strategy

### A. Avatar-model validation

Recruit consenting adult volunteers. Use a repeatable tape-measure protocol. For each person:

1. Record actual height, weight and selected circumferences/lengths.
2. Create a Quick Avatar.
3. Create a Precision Avatar using available measurements.
4. Extract mesh measurements in the neutral pose.
5. Compare predicted/model-derived measurements to the actual tape values.
6. Report MAE and RMSE by measurement, not one vague overall accuracy percentage.

The sample size, participant characteristics, protocol, missing data and limitations must be reported. Investigate whether the model adequately represents varied Indian body proportions; do not assume training-distribution coverage.

### B. Fit-engine validation

Use real T-shirts in multiple sizes, not only synthetic fixtures. Record body measures, actual garment dimensions, model recommendation and wearer's assessment by zone. Evaluate:

- top-1 correct size rate;
- top-2 recommendation rate;
- per-zone classification agreement;
- false comfortable-fit recommendation rate;
- no-suitable-size detection;
- agreement between recommendation and wearer-reported fit.

False “comfortable” results for tight garments are particularly serious.

### C. Required synthetic unit-test scenarios

Synthetic fixtures are useful for deterministic tests but must be labelled synthetic, not real-world evidence.

1. Smaller body + oversized garment → loose verdict.
2. Larger chest + smaller garment → tight chest and a justified size-up recommendation.
3. Acceptable chest + insufficient body length → chest acceptable but length flagged.
4. Same measurements, different slim/regular/oversized intent → different target-ease comparison.
5. Same buyer across multiple sizes → stable ranked list with zone reasons.
6. Incomplete seller measurement data → lower confidence, restricted evaluation or explicit unavailable result.
7. No acceptable size → `NO_SUITABLE_SIZE` plus closest warned alternative.
8. Flat width and full circumference are never silently mixed.
9. Missing or estimated body measures never masquerade as tape-measured facts.
10. Repeated model parameter inputs produce reproducible mesh/measurement output within a documented tolerance.

### D. Real end-to-end acceptance

A successful backend demonstration must show:

- real model inference from user-supplied body settings;
- a valid generated mesh/GLB;
- actual extracted measurements or direct user measurements with provenance;
- seller product and size-variant measurements;
- deterministic fit result with per-zone arithmetic;
- correct no-suitable-size behaviour;
- authorized asset retrieval;
- tests, reproducible setup and complete documentation.

Screenshots, hardcoded JSON and pre-rendered meshes do not prove the system works.

## 15. Roadmap and phase gates

| Phase | Objective | Exit gate |
|---|---|---|
| 0 | Anny vs OxiHuman feasibility, licensing, hardware, local controls, anthropometry and GLB experiments | Reproducible real inference and evidence-based model recommendation; unresolved blockers explicit |
| 1 | Freeze core architecture, schemas, contracts and repo scaffolding | Architecture/API/database specifications reviewed; no coding beyond scaffolding without approval |
| 2 | Build selected avatar adapter and mesh export | Real model-generated mesh loads in independent viewer and existing viewer contract is defined |
| 3 | Build BICE mapping and calibration data/optimizer | Demonstrable, repeatable control-to-shape behaviour; residuals and limitations reported |
| 4 | Implement anthropometry and measurement protocol | Measurement definitions, units, landmarks, reproducibility and initial tape validation documented |
| 5 | Build seller product, size-variant and garment measurement system | Seller can enter validated actual per-size T-shirt specs with flat/full convention explicit |
| 6 | Build deterministic Honest Fit Engine | Unit/property tests pass; per-zone scoring and no-suitable-size work |
| 7 | Fit report, GLB/zone metadata and API integration | End-to-end flow works independently of frontend, with authorization and tests |
| 8 | Real-world validation and refinement | Volunteer/garment-trial evaluation reported with MAE/RMSE and fit metrics |
| 9 | Frontend integration handoff and deployment | Existing React app consumes versioned APIs and GLB without being rebuilt |
| 10 | Broader WearWise intelligence and advanced simulation | Prioritize based on validated product value and feasibility |

Do not skip a phase because an AI coding agent says the code has been generated. Each phase requires test evidence and a documented exit decision.

## 16. Antigravity governance

### Responsibility split

**ChatGPT — product/technical decision owner**

- Own product requirements, scope, research, model selection, licensing decisions, architecture and trade-offs.
- Design calibration and fit mathematics, schemas, APIs and test criteria.
- Produce exact implementation prompts.
- Review Antigravity's code, claims, tests, dependencies and generated artifacts.
- Decide whether to approve, reject, revise or advance a phase.

**Antigravity — implementation and experiment executor**

- Inspect the actual repository and machine environment.
- Perform only the assigned research/experiments/implementation.
- Run real inference and tests; save outputs and logs.
- Write modular code and documentation.
- Report actual results, failures, skipped tests and unresolved issues.
- Never silently change the architecture or substitute mocks for real functionality.

**Project owner**

- Run the prompts, provide feedback and share the implementation plan/results with ChatGPT.
- Approve major product-level changes when requested.

### Permanent engineering rules

1. Read and follow the approved master specification and current phase prompt.
2. Never modify/rebuild the existing frontend during backend/POC work.
3. Never invent model capabilities, API signatures, measurement values, benchmarks or test results.
4. Never call mock or synthetic output “real model inference” or real-world validation.
5. Keep model-specific code behind adapters.
6. Keep the fit engine independent of the selected 3D body model.
7. Keep final fit arithmetic deterministic and unit-tested; an LLM must not decide the fit verdict.
8. Every measurement has an explicit unit, method and provenance.
9. Never commit restricted model assets or secrets.
10. Audit source, weights, meshes, morph targets and dependency licences separately.
11. Every critical module needs tests and acceptance criteria.
12. Report successful, failed, skipped, mocked and real-model tests separately.
13. Do not add dependencies or change the design without a clear reason and approval.
14. Do not introduce microservices without measured operational need.
15. Stop at the end of each assigned phase and wait for technical review.

### Antigravity operating cycle

**Explore → Plan → Review → Build one module → Verify → Document → Technical review → Next task**

Use Planning mode for research and architecture. Parallel agents may research or independently review, but do not let several agents simultaneously edit the same core modules. A single implementation agent owns code changes.

---

# 17. Immediate assignment — Phase 0 model feasibility

**This is the only Antigravity assignment to issue now.** Do not ask it to build the complete backend. Do not freeze Anny or OxiHuman before running the experiments below.

Copy the entire prompt in the next section into Antigravity Planning mode after opening an isolated workspace named `WEARWISE-BODY-ENGINE`.

## Ready-to-paste Antigravity prompt

```text
WEARWISE — PHASE 0: BODY MODEL FEASIBILITY, LICENSING AND HARDWARE VALIDATION

ROLE AND AUTHORITY
You are the experiment and implementation executor for this assigned Phase 0 task. ChatGPT is the product architect and technical decision owner. You must not independently freeze the production model or redesign the overall architecture. Your responsibility is to inspect the environment, conduct reproducible experiments, collect evidence, write the POC code required for those experiments and deliver a research report.

Read the complete WearWise Master Project Brief and all instructions supplied by the project owner. The project is an AI fashion and Honest Fit platform. The immediate problem is whether a user can create a useful, editable, measurement-grounded 3D body representation without a photograph, camera or body scan.

PROJECT REQUIREMENTS
- The avatar is a proportionally accurate, realistic human with neutral mannequin appearance.
- User inputs include height, weight, optional tape measurements, presets, descriptive shape attributes and regional sliders.
- Main editing groups: upper body, torso, arms and lower body, with detailed adjustments where the candidate supports them.
- Required regional investigations: shoulders, torso/chest, abdomen, waist, upper/lower arms, hips, thighs and calves.
- The avatar must ultimately support measurement extraction and GLB export for a separate React + Vite / Three.js / React Three Fiber frontend.
- The avatar is for clothing fit, not just visual customization.
- Do not ask for or require photographs, scans or camera input.

HARDWARE / COST CONSTRAINTS
Target machine, as reported by the project owner:
- NVIDIA RTX 3050, 4 GB VRAM
- AMD Ryzen 7 6800H CPU
- 16 GB RAM
- Windows development environment unless inspection proves otherwise
- Initial infrastructure budget ₹0

These are reported constraints, not verified environment facts. Inspect the actual machine before installing anything. Do not assume a CUDA version or GPU compatibility.

WORKSPACE ISOLATION
Use a dedicated workspace/repository named WEARWISE-BODY-ENGINE. If this workspace does not exist, create it in an isolated location. Do not modify the existing WearWise frontend or backend. Do not overwrite any existing project. This is a temporary research/POC workspace, not permission to create another production microservice.

PHASE 0 IS A TECHNICAL GATE. DO NOT IMPLEMENT THE COMPLETE PRODUCTION BACKEND.

CANDIDATE A — ANNY
Official repository: https://github.com/naver/anny
Official shape docs: https://naver.github.io/anny/build/shape_parameterization.html

Investigate the current official version, installation procedure, source code, native model assets, parameterization, anthropometry, dependencies, licences and asset provenance. Public documentation currently identifies v0.6.2, Python >=3.10 and PyTorch >=2.0, but verify the current repository and package metadata at execution time.

Mandatory restrictions:
- Use only Anny's native topology/assets for the POC.
- Do NOT install or use Anny's SMPL/SMPL-X optional topology, SMPL-X files or any other restricted SMPL-family model assets.
- Do NOT expose ethnicity/race-coded phenotype parameters in WearWise UI design.
- Do not assume a local-change parameter maps to an exact requested centimetre value. Measure its true effect.
- Audit the licence of code, each model asset and transitive dependency independently; Apache-2.0 code does not automatically clear every bundled asset.

CANDIDATE B — OXIHUMAN
Repository: https://github.com/cool-japan/oxihuman
Docs: https://docs.rs/oxihuman/latest/oxihuman/
Browser playground: https://play.cooljapan.dev/human

Investigate the current repository status, version/release status, source, Rust/WASM build, parameter/morph target inventory, measurement-fitting algorithm, anthropometry, mesh topology, GLB export, browser integration, asset provenance and licences. Repository files currently label v0.2.1 as unreleased; verify this directly. Treat published vertex counts, morph-target counts, test counts, benchmark timings and self-test errors as repository claims until independently reproduced.

Do not assume OxiHuman offers independent shoulder, abdomen, arm, thigh and calf adjustment simply because it exposes girth/measurement fitting. Test the exact capabilities.

EXPERIMENT 0 — MACHINE AND DEPENDENCY INVENTORY
Before installing packages, record:
1. OS and architecture.
2. Python versions and virtual environments.
3. CPU model and core count.
4. RAM and available disk space.
5. NVIDIA driver, GPU model and VRAM.
6. CUDA availability/version.
7. Existing PyTorch version and CUDA status, if any.
8. Rust and wasm toolchain availability for OxiHuman.
9. Existing workspace tree; do not modify unrelated repositories.
10. Potential version/dependency conflicts.

Create an isolated environment per candidate if that is required. Avoid installing every optional dependency. Record exact commands, package versions and environment-lock files.

EXPERIMENT A — ANNY REAL INFERENCE
Install the native Anny package using its current official documented instructions. Generate actual meshes from model inference, not stock meshes, downloaded examples, screenshots, hardcoded vertices or a manually built mannequin.

Required outputs:
1. Model initialization succeeds or a complete failure log.
2. Actual neutral/reference-pose mesh.
3. Vertex count, face count, coordinate scale and topology summary.
4. Full list of available phenotype parameters and local-change parameters.
5. At least five genuinely different actual generated body variations.
6. GLB exports for the baseline and at least two variants.
7. Independent GLB validation (parse with a separate library and/or open in an independent viewer).
8. Reproducible script and saved parameter sets.
9. Identify whether the output is a full body mesh, its supported morphology and any limitations relevant to a neutral mannequin.

EXPERIMENT B — ANNY PARAMETER BEHAVIOUR
For each available relevant parameter, generate a baseline and then change exactly one parameter at a time:
- height
- weight
- muscle
- proportions
- shoulder distance
- torso width
- abdomen/stomach shape
- waist circumference modification
- upper-arm dimensions
- lower-arm dimensions
- hip dimensions
- thigh dimensions
- calf dimensions

Also test left/right controls independently where the model exposes them.

For every experiment:
1. Save the exact baseline and changed parameter values.
2. Generate real meshes from inference.
3. Record per-vertex displacement and regional displacement where feasible.
4. Record resulting anthropometric changes using the available extraction method.
5. Quantify spillover into unrelated regions.
6. Inspect for implausible anatomy, holes, self-intersections or mesh artefacts.
7. Report whether a control is directional, nonlinear, coupled or genuinely local.

Create a parameter-behaviour matrix. Do not infer behaviour from parameter names.

EXPERIMENT C — ANNY ANTHROPOMETRY
Evaluate at minimum:
- height
- chest/bust circumference
- waist circumference
- hip circumference
- shoulder breadth
- upper-arm circumference
- lower-arm circumference if feasible
- thigh circumference
- calf circumference
- relevant torso and limb lengths

For every output record:
- whether it is directly supported or custom-developed;
- the unit and conversion, if any;
- anatomical landmark and cross-section/plane definition;
- neutral-pose assumption;
- reproducibility;
- known failure modes;
- whether it is a direct geometric measurement or a model estimate.

Do not report BMI or volume-derived weight as verified personal ground truth. If Anny's built-in module only supports a limited subset, state that explicitly. Do not fabricate unsupported measurements.

EXPERIMENT D — OXIHUMAN REAL CAPABILITY
Build/run the actual current candidate where feasible. Verify the available source and version before relying on repository claims.

Required tests:
- actual generated mesh and topology;
- exact morph-target/parameter inventory;
- independent tests for shoulder, chest/torso, abdomen, waist, arms, hips, thighs and calves;
- measurement-fitting inputs and outputs, including algorithm, bounds, optimizer and residuals;
- anthropometric units/landmarks;
- GLB export, mesh parsing and independent viewer validation;
- browser/WASM build and integration feasibility;
- whether its mesh is suitable for our neutral mannequin and eventual fit-zone overlays;
- documented adult/age/morphology limitations;
- licensing and asset provenance.

Reproduce any repository-published synthetic/self-consistency tests where practical. Label them as synthetic self-tests. They are NOT external human validation.

EXPERIMENT E — HARDWARE / PERFORMANCE
For every viable candidate, measure CPU and CUDA (if compatible) separately:
- model/build initialization time;
- first inference time;
- subsequent inference time over a repeated workload;
- peak GPU memory where measurable;
- system RAM use;
- mesh export time;
- GLB file size;
- stability across repeated requests;
- browser/WASM load and inference latency if relevant.

Report warm/cold behaviour and exact machine/environment. Do not alter CUDA/PyTorch in a way that damages the environment. If GPU fails, capture the exact failure and try CPU.

EXPERIMENT F — LICENSING AND PROVENANCE
For each candidate, audit separately:
- source-code licence;
- base mesh licence;
- morph-target licence;
- pretrained weights/model data licence;
- example assets;
- third-party assets;
- dependencies with restrictive licences;
- redistribution and commercial-hosting conditions;
- attribution/notice obligations.

Create a licence table with source links and a PASS / FAIL / UNRESOLVED status for commercial use. Unclear is not PASS. Keep any restricted files out of Git and out of the product build. Do not use SMPL/SMPL-X or SHAPY restricted assets for this POC unless the relevant licence expressly permits the specific use.

MEASUREMENT PROTOCOL
Use a consistent neutral pose and document axis orientation, coordinate scale, landmarks and units. The production app needs centimetres for body/garment dimensions, but do not assume either model emits centimetres. Verify conversions with known model dimensions and reproducible calculations.

Do not claim anthropometric accuracy merely because a model fits its own synthetic targets. External tape-measure validation is a later phase and must be performed with consenting volunteers.

DELIVERABLES
Create this structure:

WEARWISE-BODY-ENGINE/
  README.md
  docs/research/
    PHASE_0_RESEARCH_REPORT.md
    MODEL_COMPARISON.md
    ANNY_PARAMETER_ANALYSIS.md
    OXIHUMAN_PARAMETER_ANALYSIS.md
    ANTHROPOMETRY_ANALYSIS.md
    HARDWARE_BENCHMARKS.md
    LICENSE_AUDIT.md
    RISKS_AND_LIMITATIONS.md
  experiments/
    anny/
    oxihuman/
    outputs/
  benchmarks/
  artifacts/
    meshes/
    glb/
    screenshots/
  tests/
    test_model_generation.py (or equivalent candidate test)
    test_mesh_validity.py
    test_parameter_changes.py
    test_export.py
  environment files / exact reproducible setup instructions

Every report must distinguish:
- facts confirmed from official documentation/source;
- actual local experimental results;
- repository-reported claims not independently reproduced;
- engineering inferences;
- assumptions;
- unresolved questions.

PHASE 0 ACCEPTANCE CRITERIA
Do not mark Phase 0 complete just because packages installed. At minimum:
1. Real inference succeeds for at least one candidate, or failure is fully documented.
2. At least five genuine model-generated variations are saved for the viable candidate.
3. Relevant local edits have been tested one parameter at a time.
4. Mesh validity and coordinate scale are checked.
5. GLB export is validated independently.
6. Anthropometric capabilities, units and limitations are documented.
7. CPU/GPU or browser performance is benchmarked as applicable.
8. Source, model asset and dependency licensing is audited.
9. Anny and OxiHuman are compared against the same WearWise criteria.
10. Known limitations and outstanding blockers are explicit.

FINAL REPORT MUST ANSWER
1. Can Anny run reproducibly on the target machine?
2. Can it generate a valid neutral mannequin mesh and export a usable GLB?
3. Which regional parameters actually work independently?
4. What is the measured regional spillover for each tested control?
5. Which measurements are genuinely extractable, with what landmarks and units?
6. What is the runtime and memory cost?
7. Is every required code/asset/dependency commercially usable?
8. Can OxiHuman meet the same detailed customization and measurement requirements?
9. Which candidate is best for WearWise and what evidence supports that conclusion?
10. What remains unproven and what should the next experiment be?

STRICTLY OUT OF SCOPE
Do NOT build:
- the complete WearWise backend;
- authentication or production database;
- seller dashboard;
- full Honest Fit Engine;
- complete frontend or frontend changes;
- production calibration optimizer;
- a newly trained body model;
- image-based body estimation;
- physical cloth simulation.

Do not create mock meshes or fabricated measurements to make the demo look successful. Minimal scripts and tests required to run the feasibility experiments are allowed.

STOP after Phase 0. Do not proceed to production architecture or implementation until ChatGPT reviews the report, raw outputs, scripts and test evidence.
```

## 18. What happens after Phase 0

When Antigravity returns its Planning-mode execution plan, review it against the Phase 0 assignment before approving installation or code changes. After it completes, bring back its complete report, logs, parameter tables, benchmark results, license findings, actual GLB assets and test outputs. The next decision will be made from evidence, not from whichever model looks most impressive in a screenshot.

The immediate goal is a proven avatar/measurement foundation. The next implementation prompts will be issued only after that gate is passed or a documented fallback is selected.

---

## 19. Research references for the project

The following are starting points and official/research references. Re-check versions and licences before integration; a paper citation is not permission to reuse its code, weights, dataset or assets.

### Body models and shape estimation

- Anny repository: https://github.com/naver/anny
- Anny shape parameterization: https://naver.github.io/anny/build/shape_parameterization.html
- OxiHuman repository: https://github.com/cool-japan/oxihuman
- OxiHuman documentation: https://docs.rs/oxihuman/latest/oxihuman/
- OxiHuman browser playground: https://play.cooljapan.dev/human
- SMPL official project/licensing: https://smpl.is.tue.mpg.de/
- SHAPY official project/licensing: https://shapy.is.tue.mpg.de/
- BodyTalk project: https://bodytalk.is.tue.mpg.de/
- SCAPE background: https://ai.stanford.edu/~drago/scape/

### Garment shape, fit and deformation

- SIZER research: https://virtualhumans.mpi-inf.mpg.de/sizer/
- TailorNet research: https://virtualhumans.mpi-inf.mpg.de/tailornet/
- FIT (2026) project/research: https://johannakarras.com/FIT/
- 2026 interpretable multi-dimensional apparel fit framework: https://www.mdpi.com/2673-7248/6/3/75

### Textile testing references

- ASTM D3107, stretch properties of woven stretch fabrics: https://www.astm.org/d3107-26.html
- ASTM D2594/D2594M, stretch properties of low-power knitted fabrics: https://www.astm.org/d2594_d2594m-21.html

### Original product vision source

- `WearWise_Master_Project_Concept.pdf` in the project Library: source for progressive personalization, free browsing, Style DNA, personal colour, Compare My Looks, What If, Complete My Look, occasion styling, My Wardrobe, feedback learning and the original product loop.

---

**Working rule going forward:** one authoritative product direction, one approved technical decision owner, one implementation task at a time, and no advancement without evidence-based phase review.
