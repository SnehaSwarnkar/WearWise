# WEARWISE-BODY-ENGINE

**WearWise AI Fashion & Honest Fit Platform — Core Engine & Backend**  
*MVP Release (Phase 6B Accepted Baseline)*

---

## Workspace Purpose & Authority

This repository is the authoritative computational engine, domain model, database migration, and backend API workspace for **WearWise**.
- **Authority:** ChatGPT is the technical decision owner and product architect; Antigravity is the experiment and implementation executor.
- **Master Documentation:** For full system architecture, prerequisites, quickstart, frontend integration, and operational workflows, refer to the root [`../README.md`](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/README.md).
- **Authoritative Branch:** `noTouch`

---

## Engine Roadmap & Milestones

| Phase | Milestone | Status | Key Deliverable / Decision |
|---|---|---|---|
| **Phase 0** | Feasibility & Foundation | **Accepted** | NAVER Anny v0.6.2 selected over OxiHuman; CPU ($20.8\text{ ms}$) validated. |
| **Phase 1** | Architecture & Specifications | **Accepted** | Modular Monolith, BICE design, Anthropometry spec, Honest Fit spec Rev 1.2.1. |
| **Phase 4A** | Avatar Generation Pipeline | **Accepted** | Native Anny topology generation (27,420 triangles), binary GLB exporter. |
| **Phase 4B** | Anthropometric Extraction | **Accepted** | Bounded slicing, mesh-topology provenance for degree-four nodes, landmark detection. |
| **Phase 5A** | Honest Fit Engine | **Accepted** | Regional dimensional ease, six-tier fit classification, composite scoring, single recommended size. |
| **Phase 6A** | Backend Vertical Slice | **Accepted** | FastAPI Modular Monolith, Alembic initial migration (12 tables), JWT verification, SQLite WAL. |
| **Phase 6B** | Frontend Integration | **Accepted** | React 19 + TypeScript + Three.js SPA, $R_x(-90^\circ)$ glTF Y-up conversion, compact camera framing. |
| **MVP** | Final Release & Operational Readiness | **Accepted** | Automated 5-module E2E browser flow, 403 Pytest / 8 Vitest passing, production readiness audit. |

---

## Directory Structure

```text
WEARWISE-BODY-ENGINE/
├── alembic/                         # Alembic database migrations
│   └── versions/
│       └── 001_initial_schema.py    # Authoritative 12-table schema baseline
├── alembic.ini                      # Alembic environment configuration
├── app/                             # Core Application Package
│   ├── anthropometry/               # Bounded slicing & landmark extraction
│   ├── api/                         # FastAPI routes, schemas, and security adapters
│   │   ├── app.py                   # FastAPI entrypoint, CORS, exception handlers
│   │   ├── auth.py                  # Cryptographic JWT & development auth adapter
│   │   └── v1/                      # Versioned REST endpoints (profiles, avatar, garments, fit)
│   ├── avatar_engine/               # AvatarEngine protocol & NAVER Anny adapter
│   ├── config.py                    # Centralized settings & environment variables
│   ├── db/                          # SQLAlchemy database models and session factory
│   ├── domain/                      # Pure domain entities, value objects, and taxonomies
│   ├── fit/                         # Honest Fit calculation, ease rules, and scoring
│   ├── repositories/                # Persistence repository interfaces & implementations
│   ├── services/                    # Application service orchestration layer
│   └── storage/                     # Content-addressable asset storage
├── artifacts/                       # Verification artifacts & release packages
│   ├── mvp/                         # MVP release packet, manifest, and demonstration logs
│   └── phase6b/                     # Phase 6B acceptance packet & baseline screenshots
├── benchmarks/                      # Hardware performance and latency logs
├── data/                            # Local database (wearwise.db) and GLB asset storage
├── environments/                    # Pinned Python requirements and environment definitions
├── scripts/                         # Verification, packaging, and demonstration scripts
│   ├── demo_mvp_workflow.py         # Playwright automated 5-module E2E test script
│   └── rebuild_mvp_packet.py        # Authoritative release archive packager
└── tests/                           # 403 Pytest regression verification test suite
    ├── anthropometry/
    ├── api/
    ├── architecture/                # Strict architectural layer boundary tests
    ├── avatar_engine/
    ├── db/
    └── fit/
```

---

## Quick Commands

### Run Backend Tests (403 Tests)
```powershell
.\.venv-anny\Scripts\python.exe -m pytest tests/ -q
```

### Start API Server
```powershell
.\.venv-anny\Scripts\python.exe -m uvicorn app.api.app:app --host 127.0.0.1 --port 8000
```

### Run Database Migrations
```powershell
.\.venv-anny\Scripts\python.exe -m alembic upgrade head
```

### Run E2E Verification Workflow
```powershell
.\.venv-anny\Scripts\python.exe scripts/demo_mvp_workflow.py
```
