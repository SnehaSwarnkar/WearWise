# WearWise — Dual-Mode Virtual Try-On, Portal RBAC & Anthropometric Fitting Platform

**WearWise** is a full-stack digital apparel platform uniting:
- **Deterministic Body & Fit Intelligence (`WEARWISE-BODY-ENGINE/`):** Engine-neutral Body Intelligence (`BICE`), closed-loop **NAVER Anny v0.6.2** parametric avatars, exact triangle-mesh-plane anthropometry (`AnthropometryEngine`), `HonestFitEngine` ease scoring, and 5-gate Pattern-First 3D garment twins (`M2R-C`).
- **Real-Time Browser Cloth Simulation (`frontend/`):** React 19 + TypeScript + Three.js WebGL viewport running an off-main-thread Web Worker **XPBD** cloth solver (`WeldedClothSolver.ts`, `3,145` particles, `18,288` constraints) paired with broad-phase bone capsules, swept CCD, and narrow-phase mesh collisions (`AnatomicalCollider.ts`).
- **Dual-Mode Marketplace & Portal-Separated RBAC (`backend/` + `frontend/`):** Separate **Shopper** and **Seller** portals (`shopper`, `seller`, `admin`) enforced via HTTP-only `ww_auth_session` cookies, double-submit `ww_csrf_token` CSRF tokens, cross-service `auth_sessions` revocation, and explicit **`tryOnCapabilities`** readiness gating (`IMAGE_ONLY`, `THREE_D_ONLY`, `IMAGE_AND_THREE_D`).

> **Canonical Evidence & Academic Reference:** See **[WEARWISE_MASTER_PROJECT_DOSSIER.md](WEARWISE_MASTER_PROJECT_DOSSIER.md)** for the full end-to-end engineering dossier, 12 Mermaid architecture diagrams, extracted algorithms/equations, IEEE literature review, hardware/XPBD benchmarks, and thesis chapter mapping.

---

## Documentation Hub

| Document | Scope |
| :--- | :--- |
| [WEARWISE_MASTER_PROJECT_DOSSIER.md](WEARWISE_MASTER_PROJECT_DOSSIER.md) | **Canonical Master Dossier:** Architecture, 12 Mermaid diagrams, equations, IEEE references, test/benchmark matrices, verified screenshots, and thesis mapping |
| [WEARWISE_PHASE13_FINAL_REPORT.md](WEARWISE_PHASE13_FINAL_REPORT.md) | **Phase 13 Final Report:** Consumer UX redesign, 8-link customer nav, multi-step Avatar onboarding, Anny gender/calibration fix, XPBD strain heatmap, and Admin Portal |
| [WEARWISE_PHASE13_CONSOLIDATED_REPORT.md](WEARWISE_PHASE13_CONSOLIDATED_REPORT.md) | **Phase 13 Auth Baseline:** Separate Shopper & Seller portals, HTTP-only cookies, CSRF, cross-service RBAC, Playwright E2E, and verification counts |
| [WEARWISE_PHASE12_1_CONSOLIDATED_REPORT.md](WEARWISE_PHASE12_1_CONSOLIDATED_REPORT.md) | **Phase 12.1 Report:** Dual-mode `tryOnCapabilities` validation, VTON provider comparison (FASHN AI v1 vs Vertex AI India), and Rev3 verification |
| [WEARWISE_PROJECT_CLEANUP_REPORT.md](WEARWISE_PROJECT_CLEANUP_REPORT.md) | **Cleanup Audit:** Phase 12 + 12.1 workspace pruning (`1,125 -> 751` files), retained baseline GLBs, and manifest |
| [WEARWISE_PHASE11_5_CONSOLIDATED_REPORT.md](WEARWISE_PHASE11_5_CONSOLIDATED_REPORT.md) | **Phase 11.5 Baseline:** Closed-loop Anny calibration (`5×3` fit matrix) and XPBD collision pass ordering fix |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Service topology, staging DB isolation, M3–M5 lifecycle, and dual-mode marketplace contracts |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Prerequisites, `.env.example` configuration, staging startup commands, portal test accounts, and VTON setup |
| [docs/SECURITY_AND_PRIVACY.md](docs/SECURITY_AND_PRIVACY.md) | Phase 13 RBAC/CSRF/cookie rules, EXIF stripping, ephemeral temp upload cleanup, and private GLB delivery |

---

## Repository Structure

```text
WearWise/
├── frontend/                          # React 19 + TS + Three.js + Web Worker XPBD (Vite dev :5173 / preview :4173 / :3000)
├── backend/                           # FastAPI Commerce API: RBAC auth, seller store APIs, products, reviews, cart, demo orders (:8001)
├── WEARWISE-BODY-ENGINE/              # FastAPI Body & Garment Engine: Anny v0.6.2, BICE, Anthropometry, Fit, M3–M5 QA, VTON (:8000)
├── docs/                              # Architecture, Development, and Security & Privacy guides
├── scripts/                           # Seeding, calibration verification, skinning audit & benchmark utilities
├── artifacts/phase12/                 # Phase 12 dual-mode desktop & mobile Playwright screenshots (9 files)
├── artifacts/phase13/                 # Phase 13 dual-portal desktop & mobile Playwright screenshots (10 files)
└── WEARWISE_MASTER_PROJECT_DOSSIER.md # Complete project dossier & academic evidence hub
```

---

## Current Application Routes & Status

| Capability | Key Route(s) | Honest Status | Notes |
| :--- | :--- | :--- | :--- |
| **3-Role Portal Auth** | `/login`, `/seller/login`, `/seller/register`, `/admin/login` | **Staging Verified** | Separate Customer, Seller & Admin sign-in flows; backend `403` cross-portal blocks; seller `pending`/`rejected` approval gating. |
| **Customer Storefront & Shop** | `/home`, `/explore`, `/shop`, `/shop/men`, `/shop/women`, `/shop/kids`, `/product/:sku` | **Staging Verified** | 8-item consumer nav, real catalog filtering, wishlist, reviews, zero developer telemetry, `tryOnCapabilities`. |
| **Avatar Studio & Onboarding** | `/avatar`, `/avatar/create`, `/avatar/dashboard` | **Staging Verified** | 4-step consumer body profile wizard, Anny closed-loop 3D synthesis (`<= 1.6 cm` error), persistent primary avatar. |
| **Interactive 3D Fitting Room** | `/try-on` (`/experimental-try-on`) | **Staging Verified** | Published garment GLBs (`/shopper-asset/{size}`), Web Worker XPBD physics, `Normal View` & `Fit Tension Heatmap`, `P0–P11` poses. |
| **Seller Console Portal** | `/seller/dashboard`, `/seller/products`, `/seller/orders`, `/seller/studio` | **Staging Verified** | Brand-scoped products/orders, `Choose Virtual Try-On Options`, 5-gate QA, `_publish_lock`. |
| **Admin Portal & Diagnostics** | `/admin`, `/admin/diagnostics` | **Staging Verified** | Seller approval/rejection workflow, product/customer moderation, platform health, audit logs & restricted QA telemetry. |
| **Image-Based Try-On (VTON)** | `/image-try-on`, `/api/v1/try-on/vton/jobs` | **Contract-Tested; Key Pending (`503`)** | Consent gate, EXIF pixel strip, FASHN AI v1 / HTTP `VTON_API_URL` adapter, `finally` temp upload cleanup; fails closed with `503` when keys are unset. |
| **Bag & Demo Checkout** | `/cart`, `/checkout`, `/order-confirmation`, `/orders` | **Staging Verified (Demo Payment)** | Canonical `ww-session-id` bag persistence; checkout persists `DEMO_NO_PAYMENT_CAPTURED` demo orders cleanly. |

---

## Quick Start (Local Staging)

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for complete setup details:
1. Copy `.env.example` to `.env` and set `MONGODB_URI` (leave `FASHN_API_KEY` / `VTON_API_URL` blank to keep Image VTON safely fail-closed).
2. Start **Body Engine** (`:8000`) and **Commerce API** (`:8001`) using `WEARWISE-BODY-ENGINE\.venv-anny\Scripts\python.exe` with `MONGODB_BODY_ENGINE_DB=wearwise_body_engine_staging` and `MONGODB_COMMERCE_DB=wearwise_commerce_staging`.
3. Start **Frontend** (`npm run dev` inside `frontend/`) and open `http://localhost:5173`.
