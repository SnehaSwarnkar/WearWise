# WearWise Implementation Roadmap & Dependency Architecture

**Project:** WearWise AI Fashion & Honest Fit Platform  
**Document:** Technical Roadmap & Testing Gates (ROA-001)  
**Revision:** 1.2.1 (Phase 2 Authorization Baseline & Explicit Package Boundaries)  
**Date:** 2026-11-23  
**Status:** Approved Technical Architecture  

---

## 1. Authoritative Implementation Dependency Graph

```mermaid
flowchart TD
    P0["Phase 0: Feasibility, Licensing & Hardware Gate<br>(COMPLETE - Anny v0.6.2 Selected)"] --> P1
    P1["Phase 1: Architecture, Schemas & API Contracts<br>(COMPLETE - Revision 1.2.1 Baseline)"] --> P2
    
    subgraph FoundationTier["Domain Foundation & Engine Interfaces"]
        P2["Phase 2: Domain Foundation & Typed Contracts<br>(CURRENT - In Progress: Entities, Taxonomies, Protocols, Schemas)"] --> P3
        P2 --> P4
        P3["Phase 3: BICE Implementation & Regularization<br>(Normalization, Bounds, Locality Loss via ShapeEvaluationPort)"] --> P4
        P4["Phase 4: Avatar Engine & Anthropometry Integration<br>(AnnyAdapter, Mesh-Plane Graph Slicer, GLB Pipeline)"]
    end

    subgraph ServiceTier["Service Logic & Fit Intelligence"]
        P4 --> P5
        P5["Phase 5: Honest Fit Engine & Physical Ease Calibration<br>(T-Shirt Wear Trials, Bounded Fit Scorer)"] --> P6
        P6["Phase 6: Persistence, Repositories & FastAPI Monolith<br>(SQLite/PostgreSQL, Outbox Pattern, Private GLB Streaming)"]
    end

    subgraph PresentationTier["Client Delivery & Validation"]
        P6 --> P7
        P7["Phase 7: Frontend Integration & Three.js Viewer<br>(React Three Fiber, Slider Hooks, GLTF Loader)"] --> P8
        P8["Phase 8: Operational Hardening & Real-Human Validation<br>(Volunteer Tape Study, Indian Demographics, Production Deployment)"]
    end
```

---

## 2. Phase-by-Phase Breakdown, Package Boundaries & Exit Gates

### Phase 2: Domain Foundation, Schemas & Core Interfaces
- **Status:** **COMPLETED & ACCEPTED (Phase 2.1 Applied & Verified)**
- **Objective:** Translate approved Revision 1.2.1 designs into executable domain entities, transport schemas, taxonomies, and abstract interfaces.
- **Strict Package Boundaries:**
  - `app/domain/entities/`: Pure framework-independent domain models and value objects (`BodyProfile`, `ProfileRevision`, `BodyMeasurement`, `BodyShapeControls`, `RegionalShapeScale`, `AvatarShapeSpec`, `MeshData`, `LandmarkData`, `RegionalDisplacementSummary`, `ShapeEvaluationResult`, and garment entities). Zero framework dependencies.
  - `app/domain/taxonomies/`: Orthogonal enum definitions (`MeasurementAcquisitionMethod`, `MeasurementValidationState`, `MeasurementLifecycleStatus`, `MeasurementAssessmentState`, presentation, and stretch enums).
  - `app/domain/interfaces/`: Abstract protocols (`AvatarEngine`, `ShapeEvaluationPort`, `LandmarkProvider`, `StorageProvider`).
  - `app/domain/exceptions/`: Structured domain exceptions for invariant violations.
  - `app/schemas/`: Separate Pydantic v2 transport models for HTTP validation (`ProfileCreateRequest`, `MeasurementRecordRequest`, `AvatarGenerateRequest`, `FitRecommendRequest`, `StandardErrorEnvelope`).
  - `app/infrastructure/models/`: SQLAlchemy persistence models are **deferred to Phase 6**.
- **Measurable Exit Gate:**
  - Test coverage over all domain entity invariant rules (rejection of non-finite floats, invalid dimensions, negative tolerances, invalid reliability weights $[0, 1]$, and control-specific safe ranges).
  - Round-trip serialization determinism tests for domain models and transport schemas.
  - Rejection of forbidden client-assigned ownership fields (`user_id`, `brand_id`).
  - Architectural dependency tests proving zero imports of FastAPI, SQLAlchemy, Anny, or PyTorch in domain packages.

### Phase 3: BICE Implementation & Parameter Regularization
- **Status:** **COMPLETED (Implemented, Tested & Verified; Optimizer Proposal Submitted)**
- **Objective:** Implement `BICE` semantic normalization, parameter solver, and locality regularization consuming `ShapeEvaluationPort`.
- **Key Deliverables:**
  - `app/bice/normalizer.py`: Map $[0.0, 1.0]$ sliders to centered offsets $[-1.0, 1.0]$ with strict monotonicity and safe range preservation.
  - `app/bice/bounds.py`: Provisional parameter-specific clamps (thighs $[-0.5, +0.5]$, belly $[-0.5, +0.7]$, shoulders $[-0.75, +0.75]$) with structured diagnostics.
  - `app/bice/mapping.py`: Versioned semantic-to-regional mapping policy with axis isolation and inverse waist definition.
  - `app/bice/validator.py`: Semantic control and anthropometric consistency checks.
  - `app/bice/locality.py`: RMSR calculation, maximum spillover loss, near-zero threshold policy ($10^{-4}\text{ m}$) with maximal penalty ($10.0$).
  - `app/bice/solver.py`: Shape specification builder and solver candidate diagnostic framework.
  - `docs/architecture/BICE_MATHEMATICAL_OBJECTIVE_PROPOSAL.md`: Formal optimizer mathematical objective specification submitted for review.
- **Measurable Exit Gate:**
  - Comprehensive unit tests covering normalizer, bounds, mapping, locality, and solver diagnostics.
  - AST isolation test proving zero imports of `torch`, `avatar_engine`, `canny`, `mesh_eval`, or ML frameworks in `app/bice`.
  - Rejection of near-zero target signal with maximal penalty $10.0$ and structured diagnostic notes.

### Phase 4: Avatar Engine & Anthropometry Integration
- **Status:** **PENDING AUTHORIZATION**
- **Objective:** Implement `AnnyAdapter` behind `AvatarEngine` and exact triangle-mesh-plane slicing in `AnthropometryEngine`.
- **Key Deliverables:**
  - `app/avatar_engine/adapters/anny_adapter.py`: CPU LBS skinning; `AnnyLandmarkProvider`; `AnnyShapeEvaluationPort`.
  - `app/anthropometry/slicer.py`: Exact mesh-plane intersection, segment stitching, degree-2 graph validation, and loop perimeter calculator.
- **Measurable Exit Gate:**
  - Intersection correctness: 100% closure rate ($\|\mathbf{p}_{\text{start}} - \mathbf{p}_{\text{end}}\| < 10^{-6}\text{ m}$) on baseline neutral meshes.
  - Landmark-guided loop selection validated across test phenotypes without hardcoded coordinate bounds.
  - Benchmark target: Avatar generation pipeline completes in $<50\text{ ms}$ on CPU worker threads.
  - Zero vertex index dependencies inside `AnthropometryEngine`.

### Phase 5: Honest Fit Engine & Physical Garment Calibration
- **Objective:** Implement dimensional ease calculation, 6-tier classification, and execute physical wear trials.
- **Key Deliverables:**
  - `app/fit_engine/ease_calculator.py`: Measurement compatibility registry and dimensional ease math.
  - `app/fit_engine/scorer.py`: Bounded composite fit scoring ($[0, 100]$) with normalized weight denominator.
  - `docs/calibration/PHASE_5_CALIBRATION_REPORT.md`: Physical wear trial report across 5 T-shirt sizes.
- **Measurable Exit Gate:**
  - Transition of T-shirt ease thresholds from `PROVISIONAL` to `CALIBRATED` supported by physical wear feedback from 20 test trials.
  - 100% test coverage over half-open interval boundaries preventing classification overlap.

### Phase 6: Persistence Layer, Orchestration & FastAPI Monolith
- **Objective:** Implement `AvatarOrchestrationService`, SQLAlchemy repositories, SQLite WAL configuration, asynchronous `asset_deletion_outbox` worker, and versioned `/api/v1` routes.
- **Measurable Exit Gate:**
  - Passing automated API test suite covering all endpoints with authenticated requests.
  - Concurrency & load-test gate: 10 concurrent requests handled with $<150\text{ ms}$ p95 latency.
  - Content-addressable blob safety test proving shared `.glb` files are not deleted when active references remain.

### Phase 7: Frontend Integration & Three.js Viewer
- **Objective:** Connect the React 19 + Vite frontend to `/api/v1` and render binary GLBs via React Three Fiber.
- **Measurable Exit Gate:**
  - Authenticated streaming of `.glb` directly into Three.js `GLTFLoader` with `withCredentials = true`.
  - Smooth interactive 3D avatar rotation at 60 FPS in Google Chrome.

### Phase 8: Operational Hardening & Real-Human Measurement Validation
- **Objective:** Conduct formal anthropometric validation study with consenting adult volunteers to evaluate model accuracy against real human bodies (including varied Indian demographics).
- **Measurable Exit Gate:**
  - Statistical error analysis (Mean Absolute Error, 95% confidence intervals) comparing avatar-derived dimensions to physical tailoring tape measurements.
  - Final operational hardening report.
