# WEARWISE-BODY-ENGINE

**WearWise AI Fashion & Honest Fit Platform**  
*Phase 0 (Validated) & Phase 1 (Architecture & Domain Design)*

---

## Workspace Purpose & Authority

This repository is an isolated research, proof-of-concept, and architectural design workspace for **WearWise**. 
- **Authority:** ChatGPT is the technical decision owner and product architect; Antigravity is the experiment and implementation executor.
- **Scope Restriction:** Phase 0 feasibility is complete and signed off. Phase 1 is design and documentation only. No production backend (`WEARWISE-CORE`), database migrations, seller portal, or frontend modifications are implemented here.
- **Phase 0 Status:** **FORMALLY CLOSED & SIGNED OFF** ([`docs/research/PHASE_0_FINAL_DECISION.md`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/docs/research/PHASE_0_FINAL_DECISION.md)).
- **Phase 1 Status:** **ARCHITECTURE & SPECIFICATIONS COMPLETE — SUBMITTED FOR REVIEW** ([`docs/architecture/PHASE_1_ARCHITECTURE_DECISION.md`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/docs/architecture/PHASE_1_ARCHITECTURE_DECISION.md)).

---

## Directory Structure

```text
WEARWISE-BODY-ENGINE/
├── README.md                                  # This document
├── .gitignore                                 # Git exclusion rules
├── WEARWISE_MASTER_PROJECT_BRIEF.md           # Master product & technical brief
├── docs/
│   ├── architecture/                          # Phase 1: Architecture, Schemas & API Contracts
│   │   ├── PHASE_1_ARCHITECTURE_DECISION.md   # Architectural Decision Record & Acceptance Matrix
│   │   ├── PHASE_0_OPEN_ITEMS.md              # Reconciled Phase 0 evidence & measurement boundaries
│   │   ├── SYSTEM_ARCHITECTURE.md             # C4 context, module boundaries, data flows, ADRs
│   │   ├── BODY_INTELLIGENCE_DESIGN.md        # BICE, domain entities, provenance, parameter bounds
│   │   ├── AVATAR_ENGINE_DESIGN.md            # AvatarEngine protocol, AnnyAdapter, GLB lifecycle
│   │   ├── ANTHROPOMETRY_SPECIFICATION.md     # Measurement dictionary, landmarks, bounded slicing
│   │   ├── HONEST_FIT_ENGINE_SPEC.md          # Ease formulation, regional fit classification
│   │   ├── DATABASE_SCHEMA.md                 # Entity relationship diagram (ERD), ANSI SQL tables
│   │   ├── API_CONTRACTS.md                   # Versioned /api/v1 REST contracts & Pydantic schemas
│   │   └── IMPLEMENTATION_ROADMAP.md          # 8-phase implementation dependency plan & gates
│   └── research/                              # Phase 0: Feasibility, Licensing & Hardware Reports
│       ├── PHASE_0_FINAL_DECISION.md          # Formal Phase 0 sign-off & technical decision record
│       ├── PHASE_0_RESEARCH_REPORT.md         # Master report answering all 10 technical questions
│       ├── MODEL_COMPARISON.md                # Scored comparative scorecard & legal gate verdict
│       ├── ANNY_PARAMETER_ANALYSIS.md         # 20-parameter behaviour & spillover analysis
│       ├── OXIHUMAN_PARAMETER_ANALYSIS.md     # 38-morph target inventory & licensing analysis
│       ├── ANTHROPOMETRY_ANALYSIS.md          # Coordinate scale (100x), landmarks, repeatability
│       ├── HARDWARE_BENCHMARKS.md             # CPU (20.8 ms) vs GPU (74.5 ms) benchmarks
│       ├── LICENSE_AUDIT.md                   # Pinned licensing audit & transitive dependencies
│       ├── RISKS_AND_LIMITATIONS.md           # Model limitations & Phase 1-4 roadmap
│       └── PHASE_0_REVISED_PLAN_v2.1.md       # Approved Revision 2.1 implementation plan
├── experiments/
│   ├── exp0_environment.py                    # Machine inventory capture script
│   ├── exp_f_license_audit.py                 # Dependency licensing audit script
│   ├── anny/
│   │   ├── exp_a_real_inference.py            # Baseline & variation mesh generation
│   │   ├── exp_b_parameter_behaviour.py       # Controlled sweeps & spillover calculation
│   │   ├── exp_c_anthropometry.py             # Scale determination & measurement extraction
│   │   └── exp_e_benchmarks.py                # CPU vs GPU latency, VRAM, and stability
│   ├── oxihuman/
│   │   └── exp_d_capability.py                # Crates.io API & morph target evaluation
│   └── outputs/                               # Raw JSON evidence logs (exp0..exp_f)
├── benchmarks/
│   └── anny_benchmarks.json                   # Machine-readable benchmark outputs
├── artifacts/
│   ├── meshes/                                # 7 real exported OBJ meshes (~984 KB each)
│   └── glb/                                   # 25 validated binary GLB files (~494 KB each)
├── tests/
│   ├── test_model_generation.py               # Initialization & forward pass tests
│   ├── test_mesh_validity.py                  # Topology, manifold, and bounds tests
│   ├── test_parameter_changes.py              # Phenotype and local displacement tests
│   └── test_export.py                         # GLB export and re-import tests
└── environments/
    └── anny/
        └── requirements.txt                   # Locked dependencies (PyTorch cu130, Anny 0.6.2)
```

---

## Phase 0 Technical Gate Summary (Completed)

- **Selected Foundation:** **NAVER Anny v0.6.2** (Native Topology).
- **Non-Selected Alternative:** **OxiHuman** (Non-selected due to BUSL-1.1 relicensing on crates.io, 404 repository, and absence of regional controls for shoulders, arms, belly, thighs, and calves).
- **Inference Speed:** **$20.82\text{ ms}$ on CPU** / $74.45\text{ ms}$ on RTX 3050.
- **Memory Consumption:** **$113.4\text{ MB}$ peak VRAM** (only $2.7\%$ of 4 GB).
- **Interactive Preview Feasibility:** Fully achievable on local CPU hardware with ₹0 cloud infrastructure cost.

---

## Phase 1 Architecture Deliverables Summary (Completed)

All 10 architecture and domain design specifications are published under [`docs/architecture/`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/docs/architecture/). The architecture establishes a Python FastAPI Modular Monolith, strict Avatar Engine adapter isolation, a 3-tier separation of body measurements vs shape controls vs morph parameters, a 5-tier provenance taxonomy, bounded anthropometric slicing algorithms, an Honest Fit ease calculation engine, an ANSI SQL relational schema, and versioned `/api/v1` REST contracts with direct binary GLB streaming.
