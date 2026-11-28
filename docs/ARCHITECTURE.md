# WearWise System Architecture

## 1. Service Topology

| Component | Path | Port | Primary Responsibilities | Persistence |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend SPA** | `frontend/` | `3000` / `4173` | React 19 UI, Three.js WebGL viewport, `clothWorker.ts` XPBD worker, canonical `ww-session-id` bag | Browser `sessionStorage` / `localStorage` |
| **Commerce API** | `backend/` | `8001` | Product catalog merge, separated seller vs VTON capability computation, customer reviews, bag (`ww-session-id`), demo orders, shopper auth | `wearwise_commerce_staging` / JSON fallback |
| **Body & Garment Engine** | `WEARWISE-BODY-ENGINE/` | `8000` | Anny v0.6.2 avatar synthesis (`104` bones), `AnthropometryEngine`, M3–M5 merchant garment lifecycle, `HonestVTONProviderAdapter` | `wearwise_body_engine_staging`, `wearwise_staging.db` |

---

## 2. Database & Asset Isolation

- **Staging Databases:** `wearwise_body_engine_staging`, `wearwise_commerce_staging`, `WEARWISE-BODY-ENGINE/data/wearwise_staging.db`.
- **Production Databases (Protected):** `wearwise_body_engine`, `wearwise_commerce`. Test suites and staging startup scripts explicitly override DB env vars to staging.
- **Protected Reference Assets:**
  - `TSH-WW-CREW-001` Rev3 S/M/L pattern-first candidates under `WEARWISE-BODY-ENGINE/artifacts/merchant_patterns/graded_m2rc/{S,M,L}/` (`S`: `8f9bd0c7...`, `M`: `9b6212ff...`, `L`: `4bc1a0cb...`).
  - `frontend/public/garments/` and `/try-on` legacy route remain preserved unmodified.

---

## 3. Consolidated Garment & 3D Simulation Baseline (M3–M5 & Phases 10–11.5)

- **Merchant Versioning & Publication (M3–M5):**
  - Immutable revision lifecycle (`draft -> needs_review -> approved -> published`) stored across 9 Body Engine MongoDB collections plus `catalog_publications` in Commerce (`publish_revision` serialized via `_publish_lock`).
  - Dual-role image separation ensures `technical_reference`-only uploads never leak to public storefront endpoints.
  - Note on 2D CAD (`DXF`/`SVG`): Upload validates panel/perimeter geometry; 3D synthesis runs via `ParametricPatternBuilder` (guided pattern engine), not direct arbitrary arbitrary DXF-to-3D extrusion.
- **Anny Parametric Avatar & Closed-Loop Calibration (Phases 10–11.5):**
  - NAVER Anny v0.6.2 (Apache-2.0) rigged `104`-bone skeleton exported as Y-up glTF.
  - 5-iteration closed-loop calibration using `AnthropometryEngine` (`weight`, `muscle`, `measure-bust-circ-incr`, `measure-waist-circ-incr`, `torso-scale-*`) achieves `< 2 cm / 2%` chest/waist accuracy on slim, athletic, petite, and neutral profiles (`PROFILE_C_BROAD_MALE` waist hits Anny's anatomical cap at `90.59 cm` vs `94.0 cm` target).
- **Dynamic Cloth Simulation (`experimental_phase10/`):**
  - Off-main-thread Web Worker (`clothWorker.ts`) executing XPBD structural + bending constraints (`WeldedClothSolver.ts`, `3,145` welded particles, `18,288` constraints) with anatomical capsule + signed collision resolution after final constraint pass (`pushFactor=0.96`) across `P0–P11` articulated poses.

---

## 4. Dual-Mode Marketplace Capabilities (`tryOnCapabilities`)

The backend separates **Seller Capability Choice** from **Platform Service Readiness** before shoppers enter any try-on flow:

1. **Seller-Configured Mode (`try_on_mode`):**
   - `IMAGE_ONLY`: Seller provides front product photo + details, runs `POST /prepare-image-tryon` (no 3D generation required), and approves/publishes.
   - `THREE_D_ONLY`: Requires generated + QA-passed S/M/L GLB assets before approval and publication; Image Try-On disabled with explanation.
   - `IMAGE_AND_THREE_D`: Enables both modes independently; each requires its own prepared assets.
2. **Authoritative Shopper Readiness Gate (`GET /api/products`, `GET /api/products/sku/:sku`):**
   - `imageTryOnEnabled` / `imageTryOnReady` is `True` **only** when:
     - `sellerImageTryOnEnabled` is `True`,
     - Garment image preparation passed (`QA != FAILED`),
     - Real storefront product photos exist, **and**
     - External VTON provider (`FASHN_API_KEY` or `VTON_API_URL`) is configured and healthy.
   - When the VTON service is unconfigured or unavailable, `IMAGE TRY-ON` renders greyed out directly on `/product/:sku` with an explicit explanation rather than routing shoppers into a broken upload flow.

---

## 5. VTON Provider Evaluation Summary (Phase 12.1)

| Provider | Quality & Categories | Cost & Latency | License & Privacy | India Billing Practicality | Adapter Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FASHN AI API v1** (`api.fashn.ai`) | High detail fidelity; `tops`, `bottoms`, `one-pieces` (`auto`) | `~$0.075` / credit (`1` credit/output); failed calls uncharged; async ~seconds–1m | Commercial license included; inputs deleted after 3 days; no training | USD Stripe card billing (requires international txn enabled) | **Integrated** in `HonestVTONProviderAdapter` (`VTON_PROVIDER=fashn` + `FASHN_API_KEY`) |
| **Google Vertex AI** (`virtual-try-on-001`) | GA retail apparel try-on + C2PA provenance | `~$0.06` / image (sync `:predict`) | Full GCP enterprise compliance; no training | **Best for India:** Google Cloud India INR + UPI + NetBanking + 18% GST (`₹15,000` RBI e-mandate rule applies to auto-debit) | Supported via external HTTP gateway / `VTON_API_URL` |
| **fal.ai** (`FASHN v1.6` / `Kling Kolors v1.5`) | High fidelity via managed endpoints | `~$0.07–0.075` / gen pay-as-you-go | Managed partner endpoints commercially cleared (vanilla IDM-VTON CC-BY-NC-SA rejected) | USD international card billing; no native UPI | Supported via `VTON_API_URL` + `VTON_API_KEY` |
