# WearWise — Dual-Mode Virtual Try-On & Digital Fitting Marketplace

WearWise is a fashion-commerce platform that lets sellers offer **Image-Based Try-On (VTON)**, **Interactive 3D Try-On**, or **Both (`IMAGE_AND_THREE_D`)** on a canonical product catalog, backed by closed-loop NAVER Anny parametric avatars, a Web Worker XPBD cloth simulator, and FastAPI + MongoDB + SQLite microservices.

---

## Documentation Hub

| Document | Coverage |
| :--- | :--- |
| [docs/ARCHITECTURE.md](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/docs/ARCHITECTURE.md) | System topology, staging DB isolation, M3–M5 versioning, Phase 10–11.5 3D/XPBD/Anny calibration baseline, dual-mode `tryOnCapabilities` |
| [docs/DEVELOPMENT.md](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/docs/DEVELOPMENT.md) | Clean-checkout prerequisites, `.env` variables, VTON provider activation, service startup (`3000`/`8000`/`8001`), and test commands |
| [docs/SECURITY_AND_PRIVACY.md](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/docs/SECURITY_AND_PRIVACY.md) | Photo consent, EXIF pixel stripping, temp upload cleanup, ownership access controls (`401`/`403`), and staging DB boundaries |
| [WEARWISE_PHASE12_1_CONSOLIDATED_REPORT.md](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE_PHASE12_1_CONSOLIDATED_REPORT.md) | Current Phase 12.1 verification results, VTON provider evaluation, and honest feature classifications |
| [WEARWISE_PROJECT_CLEANUP_REPORT.md](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE_PROJECT_CLEANUP_REPORT.md) | Complete Phase 12 + 12.1 cleanup audit, retained/removed manifests, and storage savings |
| [WEARWISE_PHASE11_5_CONSOLIDATED_REPORT.md](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE_PHASE11_5_CONSOLIDATED_REPORT.md) | Historical baseline covering closed-loop Anny calibration (`5×3` fit matrix) and XPBD collision remediation |

---

## Repository Structure

```text
WearWise/
├── frontend/                  # React 19 + TypeScript + Three.js WebGL + XPBD Cloth Worker (port 3000 / 4173)
├── backend/                   # FastAPI Commerce API: products, capabilities, reviews, cart, demo orders, auth (port 8001)
├── WEARWISE-BODY-ENGINE/      # FastAPI Body & Garment Engine: Anny v0.6.2, BICE, M3–M5 lifecycle, VTON boundary (port 8000)
├── docs/                      # Architecture, Development, and Security & Privacy documentation
├── scripts/                   # Standalone benchmark, migration, avatar export, and garment verification utilities
└── artifacts/phase12/         # Representative desktop & mobile browser E2E evidence screenshots
```

---

## Active Application Routes

| Feature | Route(s) | Status | Notes |
| :--- | :--- | :--- | :--- |
| **Marketplace & PDP** | `/explore`, `/product/:sku` | Active (Staging) | Category browsing (`T-Shirts & Tops`, `Shirts`, `Trousers`, `Jeans`, `Skirts`, `Dresses`, `Jackets`), real review empty state, dual-mode `TRY ON` chooser |
| **Interactive 3D Fitting Room** | `/experimental-try-on` | Staging | Anny 104-bone rigged avatar + Web Worker XPBD cloth + size/pose controls + shared `ww-session-id` bag |
| **Image-Based Try-On (VTON)** | `/image-try-on` | Provider-Pending Boundary | Explicit consent, EXIF strip, temp upload deletion; blocked cleanly on PDP & `/image-try-on` when external provider (`FASHN_API_KEY` / `VTON_API_URL`) is unconfigured |
| **Seller Product Studio** | `/merchant-studio` | Staging | `Choose Virtual Try-On Options` (`IMAGE_ONLY`, `THREE_D_ONLY`, `IMAGE_AND_THREE_D`), `prepare-image-tryon`, 3D generation, approval & publication |
| **Legacy Static 3D Viewer** | `/try-on` | Protected Legacy | Preserved read-only for backward compatibility |
| **Bag & Demo Checkout** | `/cart`, `/checkout`, `/order-confirmation`, `/orders` | Staging | Shared `ww-session-id` across browsing and try-on modes; demo checkout only |

---

## Quick Start (Staging)

See [docs/DEVELOPMENT.md](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/docs/DEVELOPMENT.md) for complete setup and VTON activation steps:
1. Copy `.env.example` to `.env` and populate `MONGODB_URI` cleanly.
2. Start Body Engine (`127.0.0.1:8000`), Commerce API (`127.0.0.1:8001`), and Vite frontend (`127.0.0.1:3000`).
3. Verify protected staging isolation (`MONGODB_BODY_ENGINE_DB=wearwise_body_engine_staging`, `MONGODB_COMMERCE_DB=wearwise_commerce_staging`).
