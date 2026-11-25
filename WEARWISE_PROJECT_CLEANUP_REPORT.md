# WEARWISE — PROJECT CLEANUP REPORT (PHASE 12 & PHASE 12.1)

**Date:** 2026-11-25  
**Branch:** `remediation/m2r-a-pattern-prototype`  
**Starting Commit:** `9429d52`

---

## 1. Before-and-After Repository Inventory

*(Excludes external `node_modules/`, `.git/`, `.venv-anny/`, `dist/`, `__pycache__/`, and `.pytest_cache/` environments unless explicitly noted in Phase 12 Part 1 build cache removal)*

| Stage | Tracked + Untracked Files | Approximate Footprint | Delta |
| :--- | :--- | :--- | :--- |
| **Phase 12 Pre-Cleanup Baseline** | `1,125` files *(incl. caches & `dist/`)* | `113.10 MB` | — |
| **After Phase 12 Part 1 Cleanup** | `929` files *(active caches excluded in source count after purge)* | `96.85 MB` | **`-196` files (`-16.25 MB`)** |
| **After Phase 12.1 Part D Curated Cleanup** | **`751` files** *(incl. `WEARWISE_PHASE12_1_CONSOLIDATED_REPORT.md`)* | **`74.91 MB`** | **`-198` obsolete repo files (`-22.92 MB`)** |
| **Combined Phase 12 + Phase 12.1 Reduction** | `1,125 -> 751` *(plus Phase 12.1 new tests/docs)* | `113.10 -> 74.91 MB` | **`-394` removed files (`-39.17 MB`)** |

### Documentation & Media Footprint Reduction (Phase 12.1)

| Asset Class | Before Phase 12.1 Cleanup | After Phase 12.1 Cleanup | Delta |
| :--- | :--- | :--- | :--- |
| **Markdown Documentation (`.md`)** | `57` files | **`18` files** *(17 pre-report + this consolidated Phase 12.1 report)* | **`-39` redundant/obsolete docs** |
| **Image Assets (`.png`, `.jpg`, `.jpeg`, `.webp`, `.svg`)** | `168` files | **`82` files** | **`-86` obsolete screenshots/thumbnails** |

---

## 2. Files & Directories Removed (`SAFE TO REMOVE`)

### Phase 12 Part 1 (Build Caches & Stray Stubs — `-196` files, `-16.25 MB`)

| Target Removed | Size | Justification |
| :--- | :--- | :--- |
| `38` × `__pycache__/` & `.pytest_cache/` (`157` `.pyc` files) | `1.57 MB` | Auto-regenerated Python bytecode & pytest caches |
| `frontend/dist/` | `11.62 MB` | Reproducible production bundle (`npm run build`) |
| `artifacts/WearWise_Phase9_Engineering_Audit_Packet.zip` | `3.34 MB` | Duplicate snapshot archive of tracked artifacts |
| `WEARWISE-BODY-ENGINE/.coverage` | `68.0 KB` | Reproducible coverage SQLite DB |
| `backend/package.json` | `0.2 KB` | Empty stray Node manifest inside Python service |

### Phase 12.1 Part D (Curated Artifact, Doc & Script Consolidation — `-198` files, `-22.92 MB`)

| Target Removed | Scope | Justification |
| :--- | :--- | :--- |
| Root `screenshots/` (`11` `.png` files) | Phase 8–10 walkthrough captures | Superseded by active `artifacts/phase12/` screenshots |
| `artifacts/{demonstration,m5_ab_closure,phase10_experimental,phase11}/` | Old sprint logs, JSON traces & intermediate `.glb` snapshots | Preserved canonical `PROFILE_*.glb` in `frontend/public/experimental_phase11/` and consolidated conclusions into active docs |
| `WEARWISE-BODY-ENGINE/artifacts/{mvp,phase4b,phase5a,phase6a,phase6b,screenshots}/` | Historical sprint visual dumps | Superseded by M2R-C Rev3, published staging catalog & Phase 12 verification evidence |
| `WEARWISE-BODY-ENGINE/scripts/` | One-off MVP/Phase 4–9 runner scripts (`~30` files) | Legacy setup scripts replaced by unified services & `tests/` suites |
| `15` root milestone `.md` files + `frontend/README.md` + `WEARWISE-BODY-ENGINE/README.md` | Superseded Phase 4–12 draft reports | Consolidated into `README.md`, `docs/`, `WEARWISE_PHASE11_5_CONSOLIDATED_REPORT.md`, `WEARWISE_PHASE12_1_CONSOLIDATED_REPORT.md`, and this report |
| `15` obsolete `WEARWISE-BODY-ENGINE/` docs (`PHASE_0*`, `PHASE_1*`, `PROPOSAL*`, `PHASE8*`) | Historical phase execution trackers | Consolidated architecture/API truth preserved in `WEARWISE-BODY-ENGINE/docs/{architecture,research}/` |
| `scripts/{capture_part1_walkthrough.py,verify_phase8.py,verify_phase9.py}` | Superseded milestone E2E scripts | Replaced by unit/API suites and Playwright Phase 12/12.1 E2E checks |
| `frontend/{capture_screenshots.js,record_audit_walkthrough.js,run_browser_xpbd_benchmark.js,src/assets/hero.png}` | Unreferenced root capture/benchmark JS & unused Vite template image | Not imported anywhere in active React application |

*(Historical tracked fixture directories `WEARWISE-BODY-ENGINE/artifacts/published_catalog/TSH-WW-PYTEST-22B728` and `TSH-WW-PYTEST-D32D65` remain preserved as committed git paths, while ephemeral `TSH-WW-PYTEST-381885` and temporary pytest upload artifacts generated during final verification were purged cleanly.)*

---

## 3. Retained Files & Protected Baseline Assets (`MUST PRESERVE`)

### Retained Markdown Documentation (`18` Files Total)
- **Root Entry & Governance:** [README.md](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/README.md), [WEARWISE_PHASE11_5_CONSOLIDATED_REPORT.md](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE_PHASE11_5_CONSOLIDATED_REPORT.md), [WEARWISE_PHASE12_1_CONSOLIDATED_REPORT.md](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE_PHASE12_1_CONSOLIDATED_REPORT.md), [WEARWISE_PROJECT_CLEANUP_REPORT.md](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE_PROJECT_CLEANUP_REPORT.md)
- **Active Developer Guides:** [docs/ARCHITECTURE.md](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/docs/ARCHITECTURE.md), [docs/DEVELOPMENT.md](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/docs/DEVELOPMENT.md), [docs/SECURITY_AND_PRIVACY.md](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/docs/SECURITY_AND_PRIVACY.md)
- **Core Body Engine Technical Specs (`11` files):** `WEARWISE-BODY-ENGINE/WEARWISE_MASTER_PROJECT_BRIEF.md`, `WEARWISE-BODY-ENGINE/docs/architecture/` (`7` specs: `ANTHROPOMETRY_SPECIFICATION.md`, `API_CONTRACTS.md`, `AVATAR_ENGINE_DESIGN.md`, `BODY_INTELLIGENCE_DESIGN.md`, `DATABASE_SCHEMA.md`, `HONEST_FIT_ENGINE_SPEC.md`, `SYSTEM_ARCHITECTURE.md`), and `WEARWISE-BODY-ENGINE/docs/research/` (`3` docs: `HARDWARE_BENCHMARKS.md`, `LICENSE_AUDIT.md`, `RISKS_AND_LIMITATIONS.md`)

### Protected Runtime & Baseline Assets
- **Protected Baseline Garments:** `WEARWISE-BODY-ENGINE/artifacts/merchant_patterns/graded_m2rc/{S,M,L}/TSH-WW-CREW-001_*_rev3.glb` (SHA-256 checksums verified unchanged) and preview images.
- **Public 3D & Texture Assets:** `frontend/public/garments/` (including active diffuse texture `garment_texture_diffuse.png`), `frontend/public/experimental_phase10/`, and calibrated avatars `frontend/public/experimental_phase11/` (`PROFILE_A..E.glb`).
- **Active Runtime Staging Storage:** `WEARWISE-BODY-ENGINE/artifacts/published_catalog/`, `merchant_private/`, `merchant_uploads/`, `merchant_patterns/` (`graded_m2rb`, `graded_m2rc`, `prototype_m2r`), and `phase4a` reference renders.
- **Phase 12 Verification Screenshots (`9` files):** `artifacts/phase12/01_explore_categories_desktop.png` through `09_image_tryon_mobile.png`.
- **Active Verification Suites:** `backend/tests/` (`2` test files), `frontend/src/__tests__/` (`7` Vitest files), `WEARWISE-BODY-ENGINE/tests/` (`33` pytest files), and `scripts/` staging audit/seed/verification scripts.

### Items Preserved with Explicit Audit Notes (`VERIFY BEFORE REMOVING`)
- **`data_backups/` (`4` files, `~0.25 MB`):** Staging database snapshots — retained per strict data-preservation rules.
- **`WEARWISE-BODY-ENGINE/artifacts/merchant_patterns/graded_m2rb/` & `phase4a/`:** Historical acceptance baseline comparisons referenced in master specs — retained intentionally.
- **`puppeteer` devDependency in `frontend/package.json`:** Retained rather than uninstalling so `frontend/package-lock.json` stays untouched and deterministic offline builds remain reproducible without `npm install`.

---

## 4. Final Repository Structure Summary

```text
WearWise/                            (751 files incl. report, ~74.9 MB excl. deps/caches)
├── .env.example                     (Staging DB & VTON provider env template, no secrets)
├── .gitignore                       (Ignores node_modules, dist, .venv-anny, caches, zip archives)
├── README.md                        (Root overview, port map, quickstart & status links)
├── docs/
│   ├── ARCHITECTURE.md              (Dual-mode marketplace, VTON provider comparison & DB isolation)
│   ├── DEVELOPMENT.md               (Local staging setup, test commands & VTON activation guide)
│   └── SECURITY_AND_PRIVACY.md      (Ownership, fail-closed auth, ephemeral photo handling & C2PA/ethics)
├── artifacts/phase12/               (9 verified desktop/mobile Playwright screenshots)
├── backend/                         (Commerce API: FastAPI staging DB + 7 pytest cases)
├── frontend/                        (React/Vite/R3F storefront, PDP, Image/3D Try-On + 22 Vitest cases)
├── scripts/                         (Seed, verification & audit scripts)
├── data_backups/                    (Preserved database snapshots)
├── WEARWISE-BODY-ENGINE/            (Anny Avatar, Pattern-First Garments, VTON Adapter + 409 pytest cases)
├── WEARWISE_PHASE11_5_CONSOLIDATED_REPORT.md
├── WEARWISE_PHASE12_1_CONSOLIDATED_REPORT.md
└── WEARWISE_PROJECT_CLEANUP_REPORT.md
```
