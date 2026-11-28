# WEARWISE — PHASE 13 FINAL ENGINEERING & PRODUCT REPORT

**Phase:** 13 — Complete Customer Experience Redesign, Avatar Engine Rework, Cloth Simulation Correction & Admin Portal  
**Repository:** `WearWise` monorepo (`remediation/m2r-a-pattern-prototype`)  
**Environment:** Staging (`wearwise_commerce_staging`, `wearwise_body_engine_staging`, `WEARWISE-BODY-ENGINE/data/wearwise_staging.db`) — **Production databases untouched**  
**Date:** 2026-11-26  

---

## 1. Executive Summary

Phase 13 transformed WearWise from a developer-exposed prototype into a consumer-ready fashion marketplace with strict separation across **Customer**, **Seller**, and **Admin** experiences:

1. **Elimination of Consumer-Facing Engineering Telemetry:** Removed vertex/triangle/mesh counts, manifold/Euler checks, boundary edge diagnostics, `BICE` / `ISO 7250` labels, `Anny v0.6.2` strings, `WorkerMode` telemetry, and internal QA panels from customer screens (`/home`, `/explore`, `/shop`, `/avatar/*`, `/try-on`), isolating internal diagnostics cleanly inside `/admin/diagnostics` (Admin-guarded).
2. **Customer Experience & Navigation Redesign:** Replaced cluttered legacy navigation with a clean 8-item responsive bar and mobile drawer (`Home`, `Explore`, `Shop`, `Avatar`, `Wishlist`, `Orders`, `Cart`, `Profile`), redesigned `/home` and `/explore` as fashion storefronts backed by the live Commerce product catalog (`17` base Men/Women/Kids/Unisex items plus published merchant garments), and built unified `/shop`, `/shop/men`, `/shop/women`, and `/shop/kids` shopping pages.
3. **Avatar Engine Rework & Multi-Step Onboarding (`/avatar`, `/avatar/create`, `/avatar/dashboard`):**
   - Fixed a critical root-cause bug in `AnnyAdapter`: **NAVER Anny's `gender` phenotype axis was inverted** (`masculine` mapped to `1.0` = female and `feminine` mapped to `0.0` = male, verified in `anny/models/phenotype.py` & `anny_inverter.py`). Swapped to `masculine -> 0.0`, `feminine -> 1.0`, `neutral -> 0.5`.
   - Upgraded closed-loop body calibration to `7` iterations across chest, waist, hip, and shoulder breadth with realistic adult baseline phenotypes (`weight=0.58/0.54`, `muscle=0.55/0.45`), semantic slider bindings, single-primary-profile enforcement per user, and consistent X/Z torso centering + Y=0 grounding for both unrigged and rigged GLBs.
   - Resolved live browser `403` and `422` bugs caused by dev shorthand headers overriding HTTP-only session cookies (`ww_auth_session`) and missing `current_revision` fields on `PUT /api/v1/profiles/{profile_id}/controls`.
4. **3D Virtual Try-On Cloth Simulation & Fit Tension Heatmap:** Fixed articulated elbow hinge axis computation (`applyArticulatedPoseToRig`), scaled anatomical capsules dynamically to stature & shoulder breadth, expanded pelvis/thigh hip capsules and depenetration passes, unified pose interpolation via `setExactPose`, exposed `/api/v1/merchant/garments/{garment_id}/shopper-asset/{size}` for published garment GLBs (removing the `403` shopper block on `/revisions/{rev}/assets/{size}`), and implemented `Normal View` vs `Fit Tension Heatmap` with a 4-color legend, regional comfort breakdown, and explicit simulation-estimate disclosure.
5. **Admin Portal & Seller Lifecycle Enforcement:** Built `/admin` (`Overview`, `Sellers & Approvals`, `Product Moderation`, `Orders`, `Customers`, `Platform Health`, `Audit Trail`, plus restricted `Internal Diagnostics`) backed by `/api/admin/*` endpoints, role-scoped `/login`, `/seller/login`, `/admin/login` authentication, and full Seller `pending` -> `rejected` -> re-application -> `approved` (`active`) workflows.

---

## 2. Before-and-After Architecture

| Layer | Before Phase 13 | After Phase 13 |
| :--- | :--- | :--- |
| **Role Separation** | Dual-portal (`shopper`, `seller`) with no dedicated Admin UI or backend admin governance endpoints | Three distinct portals & guards: `ShopperRoute` / public storefront, `SellerRoute` (`/seller/*`), `AdminRoute` (`/admin/*`) |
| **Customer UI** | Exposed `Vertex Count`, `Triangle Count`, `Manifold`, `BICE`, `WorkerMode`, and engineering toggles on try-on & avatar views | Clean consumer vocabulary only (`Fit Tension Heatmap`, `Relaxed / Comfortable / Snug / Tight`, body profile summary) |
| **Garment Asset Delivery** | `get_shopper_asset` pointed shoppers to `/revisions/{rev}/assets/{size}` guarded by `get_current_brand_id` (`403`) | Private `/revisions/{rev}/assets/{size}` stays brand-only; published garments serve read-only GLB via `/shopper-asset/{size}` after verifying `status == "published"` |
| **Client Auth Sync** | `DefaultDevAuthHeaderProvider` emitted `Authorization: Bearer <devUserId>` even when `ww_auth_session` cookie existed, conflicting with GLB `fetch()` calls | Suppresses dev shorthand headers whenever `ww_csrf_token` cookie exists so all API and binary GLB requests share the identical session cookie |
| **Avatar Calibration** | Inverted Anny `gender` mapping (`1.0` female / `0.0` male), single/coarse adjustment, sparse slider mapping | Corrected Anny polarity (`0.0` male / `1.0` female), `7`-iteration multi-target calibration, torso-centered & grounded rigged GLB |
| **Cloth Physics & Heatmap** | World-X elbow hinge distortion, fixed-radius capsules, worker/main-thread pose drift, no strain visualization | Humerus-rotated elbow hinge (`applyArticulatedPoseToRig`), stature-scaled + hip capsules, `setExactPose` sync, live per-particle edge strain buffer & 4-band heatmap |

---

## 3. Before-and-After Customer Experience

| Journey | Before | After |
| :--- | :--- | :--- |
| **Top Navigation** | Crowded bar exposing extra utility/experimental links | 8 clean links (`Home`, `Explore`, `Shop`, `Avatar`, `Wishlist`, `Orders`, `Cart`, `Profile`) + responsive `390px` 2x4 mobile drawer |
| **Home & Explore** | Sparse demo cards / placeholder feel | Branded fashion editorial hero, Women/Men/Kids department collections, honest catalog-based curated/trending/new sections |
| **Avatar Creation** | Confusing form mixing sliders, raw controls, and engine terminology | Guided 4-step wizard (`1. Basic Details` -> `2. Generate Model` -> `3. Fine-Tune Shape` -> `4. Save Profile`) with one primary avatar per customer |
| **Avatar Dashboard** | Generic status table | `No Saved Avatar Yet` onboarding CTA or personal `Avatar Studio` showing 3D turntable, Height/Chest/Waist/Hips/Shoulders summary, Wishlist, Orders & 3D try-on picks |
| **Virtual Try-On** | Engineering telemetry overlay & broken/empty 403 canvas for cookie-logged-in shoppers | Live 3D clothed mannequin, `Normal View` / `Fit Tension Heatmap` toggle, `P0–P11`-subset consumer poses (`Standing Natural`, `Arms Overhead`, `Elbows Bent`, etc.), clear S/M/L recommendation & comparison cards |

---

## 4. Route Map

### Customer Routes
- `/` -> redirects to `/home`
- `/home` — Consumer homepage storefront
- `/explore` — Product discovery, categories, trending & recent catalog items
- `/shop` — Full filterable shopping catalog (`search`, `category`, `gender`, `price`, `sort`)
- `/shop/men`, `/shop/women`, `/shop/kids` — Gender-scoped catalog views
- `/product/:sku` — Product detail page with size guide, capability badges (`tryOnCapabilities`), wishlist & bag actions
- `/avatar` — Avatar landing (onboarding CTA if none, or summary view if saved)
- `/avatar/create` — 4-step guided avatar creation & proportion editing wizard (`?edit=1`)
- `/avatar/dashboard` — Primary avatar studio, extracted body summary, wishlist & 3D try-on wardrobe
- `/try-on` — Consumer 3D Virtual Try-On & Fit Tension Heatmap
- `/image-try-on` — Fail-closed external Photo VTON experience
- `/wishlist` — Saved items (`Wishlist`) with SKU/category/3D capability metadata
- `/orders`, `/order-confirmation` — Order history & demo order receipt
- `/cart`, `/checkout` — Shopping bag (`ww-session-id`) & simulated staging checkout
- `/profile` — Customer account details, saved body summary, sign-out

### Seller Routes (`SellerRoute`)
- `/seller/login`, `/seller/register` — Dedicated Seller Portal authentication & merchant onboarding application
- `/seller`, `/seller/dashboard` — Seller store overview
- `/seller/products`, `/seller/products/new`, `/seller/inventory` — Product CRUD & inventory
- `/seller/studio` (`/merchant/garment-studio`, `/merchant-studio` aliases) — Digital Garment Studio
- `/seller/orders`, `/seller/profile`, `/seller/settings` — Seller fulfillment & store profile

### Admin & Restricted Diagnostic Routes (`AdminRoute`)
- `/admin/login` — Dedicated Admin Portal sign-in
- `/admin` — Full Admin Portal dashboard (`Overview`, `Sellers & Approvals`, `Product Moderation`, `Orders`, `Customers`, `Platform Health`, `Audit Trail`)
- `/admin/diagnostics` — Restricted internal geometry/simulation/QA diagnostics (blocked for non-admins via `AdminRoute`)

---

## 5. Role and Permission Model

| Role | `principal_type` (JWT) | Permitted Portals | Server Enforcement |
| :--- | :--- | :--- | :--- |
| **Customer (`shopper`)** | `shopper` | Storefront, Avatar (`/api/v1/profiles*`, `/api/v1/avatar*`), Cart, Orders, Wishlist | Blocked (`403`) from `/api/seller/*`, `/api/v1/merchant/garments/*` writes, and `/api/admin/*`; profile/GLB ownership enforced per `user_id` |
| **Seller (`seller`)** | `brand` | Seller Portal & Digital Garment Studio when `seller_approved=True` and `status="active"` | Blocked (`403`) until approved; pending/rejected/suspended sellers blocked at login & token claim validation; brand-scoped product & revision ownership |
| **Admin (`admin`)** | `admin` | Admin Portal (`/admin`, `/admin/diagnostics`) + platform governance | `require_admin` checks verified session claims + DB role/active state; non-admins receive `403` |

---

## 6. Authentication Implementation

- **Commerce API (`backend/app/core/security.py`, `backend/app/routers/auth.py`):**
  - Salted `pbkdf2_sha256` (`120,000` iterations) password hashing with backward-compatible verification for legacy SHA-256 test records.
  - Role-specific login endpoints enforcing portal separation and account state (`active`, `pending`, `rejected`, `suspended`).
  - Mints signed HS256 JWT tokens (`sub`, `commerce_user_id`, `user_id`, `principal_type`, `role`, `jti`, `iss="wearwise:auth"`, `aud="wearwise:api"`, `exp`) stored in HTTP-only `ww_auth_session` cookies alongside double-submit `ww_csrf_token` CSRF protection and revocable `auth_sessions` persistence.
- **Cross-Service Body Engine Auth (`WEARWISE-BODY-ENGINE/app/api/auth.py`):**
  - Verifies the same HS256 JWT signature (`iss`, `aud`, `exp`), checks Mongo `auth_sessions` `revoked` flag, and verifies active/approved user state.
- **Frontend Sync (`frontend/src/api/client.ts`):**
  - `DefaultDevAuthHeaderProvider.getAuthHeaders()` returns `{}` when an HTTP-only cookie session (`ww_csrf_token`) is active and no explicit override token is set, ensuring `apiClient` requests and GLB binary `fetch()` calls authenticate under the identical `ww_auth_session` user.

---

## 7. Admin System

Implemented in `backend/app/routers/admin.py`, `frontend/src/api/admin.ts`, `frontend/src/components/admin/AdminLayout.tsx`, and `frontend/src/pages/admin/AdminDashboardPage.tsx`:
- **Overview KPIs:** Live database counts for total/active customers, approved sellers, pending seller applications, active/total products, orders, simulated order volume, and honestly labeled **Captured Revenue: ₹0 (Simulated staging checkout only)**.
- **Seller Governance:** Filterable list (`pending`, `active`, `rejected`, `suspended`), **Approve**, **Reject** (with required `reason`), **Suspend**, and **Reactivate** actions persisted with audit logs.
- **Product Moderation, Orders, Customers, Platform Health & Audit Trail:** Full admin inspection tables, product visibility toggles, customer active/suspended toggles, live Commerce/MongoDB/Body Engine health probe, and chronological `admin_audit_logs`.

---

## 8. Seller Approval Workflow

1. **Application (`POST /api/auth/seller/apply`):** Collects `owner_name`, `email`, `password`, `store_name`, `phone`, `business_type`, `business_address`, and `store_description`. New merchant applications start in `status="pending"`, `seller_approved=False`.
2. **Gate Before Approval:** Attempting to sign in at `/seller/login` while `pending` or `rejected` is rejected server-side; rejected applicants see their `rejection_reason` and can re-apply cleanly.
3. **Approval (`POST /api/admin/sellers/{user_id}/approve`):** Sets `status="active"`, `seller_approved=True`, records `verified_at`, assigns `brand_id`, and logs an admin audit entry.
4. **Workspace Access:** Once approved, the seller gains full access to `/seller/dashboard`, `/seller/products`, `/seller/orders`, and `/seller/studio`.

---

## 9. Customer Experience Implementation

- **Navigation & Shell (`frontend/src/pages/Header.jsx`):** Clean top bar with the exact 8 customer destinations, theme toggle, user pill, and responsive mobile menu drawer (`data-testid="mobile-menu-toggle"`, `data-testid="mobile-nav-drawer"`). Zero dev role switches or merchant/admin links appear in customer navigation.
- **Storefront (`/home` — `Home.jsx`, `/explore` — `Explore.jsx`):** Editorial hero section, Women/Men/Kids collection cards, honest catalog-based Trending / New Arrivals / Category sections (zero fabricated AI recommendation claims), wishlist toggles, and 3D capability badges.
- **Catalog (`/shop`, `/shop/men`, `/shop/women`, `/shop/kids` — `ShopPage.tsx`, `MenShop.jsx`, `WomenShop.jsx`, `KidsShop.jsx`):** Backed by live `GET /api/products` supporting `gender`, `category`, `search`, `min_price`, `max_price`, and `sort`.
- **Saved & Orders (`SavedLooks.jsx`, `ProfilePage.tsx`, `MyOrders.jsx`, `Cart.jsx`):** Enriched wishlist items (`sku`, `category`, `try_on_mode`), customer profile & body summary, order history, and bag management.

---

## 10. Avatar Architecture

- **Endpoints (`WEARWISE-BODY-ENGINE/app/api/v1/profiles.py`, `avatar.py`):**
  - `POST /api/v1/profiles` enforces one primary active profile per `user_id` (`avatar_name`, `body_shape`, `age_range`, `presentation_gender`, `stature_cm`, `reported_weight_kg`, `initial_controls`).
  - `PATCH /api/v1/profiles/{profile_id}` supports updating metadata & height (`stature_cm`).
  - `PUT /api/v1/profiles/{profile_id}/controls` creates an optimistic-locked revision (`expected_revision`) and returns both `new_revision` and `current_revision` plus `shape_controls`.
  - `POST /api/v1/avatar/generate` produces glTF 2.0 binary (`format="glb"`, `rigged=true`), stores content-addressed bytes by SHA-256, runs `AnthropometryEngine` extraction, and updates `active_measurements`.
  - `GET /api/v1/avatar/assets/{avatar_id}.glb` streams binary GLB after verifying profile ownership.
- **Frontend Flow:** `/avatar` (`AvatarLandingPage.tsx`) -> `/avatar/create` (`AvatarCreateWizard.tsx` 4-step flow) -> `/avatar/dashboard` (`AvatarDashboardPage.tsx` with persistent primary profile & `ConsumerAvatarViewport.tsx`).

---

## 11. Avatar Generation Methodology

In `WEARWISE-BODY-ENGINE/app/avatar_engine/adapters/anny_adapter.py`:
1. **Corrected NAVER Anny Phenotype Mapping:** `masculine -> 0.0`, `feminine -> 1.0`, `neutral -> 0.5` (previous inversion caused masculine and feminine silhouettes to swap).
2. **Realistic Adult Baselines & Semantic Mapping:** Baseline phenotype (`weight=0.58/0.54`, `muscle=0.55/0.45`, `age=0.5`, `proportions=0.5`) paired with mapped anatomical controls (`shoulder_width`, `chest_fullness` including `measure-bust-circ-incr`, `belly_fullness`, `waist_definition`, `arm_fullness`, `hip_fullness`, `thigh_fullness`, `calf_fullness`).
3. **Closed-Loop Multi-Target Calibration:** Up to `7` iterative optimization passes adjusting phenotype/morph weights against target chest circumference, waist circumference, hip circumference, and shoulder breadth extracted directly from the 3D mesh.
4. **Canonical Coordinate Alignment:** `_compute_glb_alignment_shift` centers torso X/Z and grounds minimum vertex Y cleanly to `Y = 0` for both unrigged and 104-bone rigged GLB exports.

---

## 12. Avatar Measurement Validation

Measurements are extracted directly from the generated 3D triangle mesh via `AnthropometryEngine` (`WEARWISE-BODY-ENGINE/app/anthropometry/engine.py`) at canonical anatomical landmarks (`stature`, `chest_circumference`, `waist_planar_circumference`, `hip_circumference`, `shoulder_biacromial_breadth`) without faking or overriding output metrics.

---

## 13. Avatar Validation Results

Measured directly in `WEARWISE-BODY-ENGINE/tests/avatar_engine/test_avatar_accuracy_suite.py` (all 9 tests in `test_avatar_accuracy_suite.py` + 14 tests in `test_anny_adapter.py` passing):

| Profile Archetype | Target Stature (cm) | Measured Stature | Chest Error | Waist Error | Hip Error |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `M_SLIM_174` (Masculine) | `174.0` | `174.0 cm` | `-1.12 cm` (`88.88`) | `+0.61 cm` (`74.61`) | — |
| `M_AVG_178` (Masculine) | `178.0` | `178.0 cm` | `+0.64 cm` (`98.64`) | `+1.08 cm` (`83.08`) | `+0.63 cm` (`96.63`) |
| `M_BROAD_183` (Masculine) | `183.0` | `183.0 cm` | `+0.99 cm` (`110.99`) | `+1.13 cm` (`95.13`) | — |
| `F_PETITE_158` (Feminine) | `158.0` | `158.0 cm` | `-0.99 cm` (`81.01`) | `-0.86 cm` (`65.14`) | `-1.06 cm` (`90.94`) |
| `F_HOURGLASS_168` (Feminine) | `168.0` | `168.0 cm` | `+1.45 cm` (`93.45`) | `+1.09 cm` (`71.09`) | `+1.58 cm` (`101.58`) |
| `F_CURVY_170` (Feminine) | `170.0` | `170.0 cm` | `-0.35 cm` (`101.65`) | `-1.34 cm` (`82.66`) | `-0.89 cm` (`109.11`) |

- Every tested male and female multi-target preset achieved **<= 1.6 cm error** (within the `<= 2 cm / 2%` accuracy target).
- `test_rigged_glb_centered_and_grounded`, `test_masculine_vs_feminine_anatomical_distinction`, and `test_slider_presets_produce_meaningful_circumference_deltas` all passed.

---

## 14. Virtual Try-On Architecture

1. **Product Readiness Gate (`backend/app/routers/products.py`):** Evaluates `tryOnCapabilities` (`threeDTryOnEnabled`, `imageTryOnEnabled`) before offering 3D Fitting Room links.
2. **Garment Asset Resolution (`WEARWISE-BODY-ENGINE/app/api/v1/merchant_garments.py`):**
   - `GET /api/v1/merchant/garments/{garment_id}/shopper-asset?size=...` verifies `status == "published"` and returns garment measurements, fabric profile, and `/shopper-asset/{size}?revision=...`.
   - `GET /api/v1/merchant/garments/{garment_id}/shopper-asset/{size}` streams the approved GLB bytes safely for shoppers without exposing merchant-private `/revisions/{rev}/assets/{size}`.
3. **Simulation Execution (`frontend/src/experimental_phase10/`):**
   - `ExperimentalTryOnPage.tsx` aligns garment collar/chest to the avatar's `neck01`/`spine01` world positions, loads `WorkerClothClient`, synchronizes avatar bone articulation with the XPBD Web Worker (`clothWorker.ts`), and renders either `Normal View` (material appearance) or `Fit Tension Heatmap`.

---

## 15. Cloth Simulation Changes

1. **Anatomical Elbow Flexion (`WeldedClothSolver.ts` -> `applyArticulatedPoseToRig`):** Rotates the elbow flexion hinge axis (`_sharedAxisX`) by the posed humerus delta quaternion (`restUpperWorldQuats` -> current world quaternion), shared identically by main-thread skeleton visuals and the Web Worker collider.
2. **Exact Pose Synchronization (`setExactPose`):** `WorkerClothClient.ts` steps `currentPose` on the main thread and passes it verbatim via `setExactPose` so visual bones and collider geometry never diverge.
3. **Stature & Breadth Collider Scaling (`AnatomicalCollider.ts`):** Scaled capsule radii using live `heightScale` (`maxAvatarY / 1.68`) and `widthScale` (`shoulderSpan / 0.36`), removed fixed `|vx| <= 0.55` upper-body clipping (`Math.max(0.55, maxY * 0.52)`), added `pelvis_hip`, `hip_thigh_L`, and `hip_thigh_R` capsules, widened narrow-phase push-out (`dist2 <= 0.048^2`, `signedDist > -0.042`), and added a 5-pass collision depenetration pre-seat at `bindGarment` while preserving true CAD `conRestLen`.
4. **Natural Drape & Constraint Stability (`WeldedClothSolver.ts`):** Increased XPBD projection to 3 structural passes per substep (`4` substeps/step), softened gravity (`-1.25 * gravityScale`), lowered torso rest-frame pull (`recoveryStiffness * 0.20`), and computed dynamic `sleeveBlend` bounds from live avatar shoulder span.

---

## 16. Strain / Heatmap Methodology

- **Simulation Source (`WeldedClothSolver.ts`):** For every welded structural constraint (warp, weft, shear — excluding bending pairs), computes relative edge extension `ratio - 1.0` (`(currentLength / restLength) - 1.0`), averages per-particle strain into a `Float32Array` buffer transferred with each `FRAME` / `RESET_ACK`, and aggregates zone averages (`chestPct`, `shouldersPct`, `underarmsPct`, `waistPct`, `overallComfort`).
- **Color Visualization (`WorkerClothClient.ts`):** Maps per-particle strain smoothly onto vertex colors when `Fit Tension Heatmap` is active:
  - **Blue (Relaxed / Loose drape):** `strain < -0.8%`
  - **Green (Comfortable drape):** `-0.8% <= strain <= +2.2%`
  - **Amber (Fitted / Snug):** `+2.2% < strain <= +4.8%`
  - **Red (Tight / High simulated tension):** `strain > +4.8%`
- **Honest UI Disclosure (`ExperimentalTryOnPage.tsx`):** Displays a 4-color legend, zone breakdown, and clear customer copy explaining that heatmap colors are derived from **simulated cloth mesh edge stretch** rather than physical textile tensile laboratory testing.

---

## 17. Limitations

1. **External Image VTON (`503`):** Without `FASHN_API_KEY` or `VTON_API_URL` configured, Image Try-On fails closed (`503`).
2. **Garment Sizing vs. Body Shape:** In 3D Virtual Try-On, `TSH-WW-PHASE11-ACCEPTANCE-001` uses fixed S/M/L CAD block meshes fitted to canonical proportions rather than dynamically re-grading garment pattern geometry per individual body shape.
3. **Observed Hip Clipping & Arm-Raise Stripe Artifacts:** As verified visually in `04_tryon_strain_heatmap.png` when testing Size M of a male-proportioned tee on a petite curvy Hourglass avatar (`165 cm`, `108 cm` hips) with `P3 Arms Overhead` (`138°` shoulder raise), minor lower-left hip hem clipping and horizontal amber/red strain striping still appear under extreme overhead pose lift.
4. **Simulated Staging Checkout:** Orders and revenue use staging simulated checkout (`Captured Revenue: ₹0`); no live payment gateway is attached.

---

## 18. Security Changes

- Eliminated client-side shopper/merchant role switching from consumer UI.
- Preserved strict `Depends(get_current_brand_id)` protection on `/api/v1/merchant/garments/{garment_id}/revisions/{revision}/assets/{size}` while serving approved published binaries separately through `/shopper-asset/{size}`.
- Fixed `DefaultDevAuthHeaderProvider` so browser sessions with `ww_csrf_token` never inject fallback dev Bearer headers over real HTTP-only `ww_auth_session` cookies.
- Enforced `require_admin` across all `/api/admin/*` endpoints and `AdminRoute` across `/admin` & `/admin/diagnostics`.
- Preserved `AuthContext` cross-service `jti` revocation checks and CSRF double-submit enforcement on unsafe methods.

---

## 19. MongoDB & SQLite Schema Changes

- **SQLite / SQLAlchemy (`WEARWISE-BODY-ENGINE/app/db/models.py`, `db/session.py`):**
  - Added `avatar_name` (`String(80)`), `body_shape` (`String(48)`), and `age_range` (`String(32)`) to `body_profiles` (`BodyProfileModel`) with safe runtime `ALTER TABLE` migration for existing staging DBs.
- **Commerce MongoDB / JSON Store (`users`, `admin_audit_logs`, `seller_products`, `saved`):**
  - Added `"rejected"` status, `owner_name`, `phone`, `business_type`, `business_address`, `rejection_reason`, and `verified_at` fields on `users`.
  - Added `admin_audit_logs` collection recording admin seller/product/customer governance actions.
  - Added `sku`, `category`, and `try_on_mode` metadata on wishlist items.

---

## 20. API Changes

- **Auth (`backend/app/routers/auth.py`):** Added role-scoped login routes (`/api/auth/customer/login`, `/api/auth/seller/login`, `/api/auth/admin/login`), updated `/api/auth/seller/apply` to support `{ owner_name, phone, business_type, business_address, store_name, ... }` & re-application after rejection.
- **Admin (`backend/app/routers/admin.py`):** Added `/api/admin/overview`, `/api/admin/sellers`, `/api/admin/sellers/{id}/approve`, `/reject`, `/suspend`, `/reactivate`, `/api/admin/products`, `/api/admin/products/{id}/status`, `/api/admin/orders`, `/api/admin/customers`, `/api/admin/customers/{id}/status`, `/api/admin/health`, and `/api/admin/audit-logs`.
- **Products & Wishlist (`backend/app/routers/products.py`, `saved.py`):** Expanded catalog (`17` base items preserving IDs `1..9`), added `gender`, `occasion`, `search`, `min_price`, `max_price`, `sort`, fixed `/api/products/recommendations`, enriched wishlist response fields.
- **Body Engine (`WEARWISE-BODY-ENGINE/app/api/v1/profiles.py`, `merchant_garments.py`):** Added `avatar_name`, `body_shape`, `age_range` support, editable `stature_cm`, single primary profile per `user_id`, `current_revision` + `shape_controls` in `PUT /profiles/{id}/controls`, and `GET /api/v1/merchant/garments/{garment_id}/shopper-asset/{size}`.

---

## 21. Frontend Changes

- **Routing & Guards (`src/App.tsx`, `src/components/PortalAccessDenied.tsx`):** Added `AdminRoute`, updated `ShopperRoute` / `SellerRoute` boundaries, mapped `/home`, `/explore`, `/shop`, `/shop/men`, `/shop/women`, `/shop/kids`, `/avatar`, `/avatar/create`, `/avatar/dashboard`, `/admin`, `/admin/login`, `/admin/diagnostics`.
- **Storefront & Nav:** Redesigned `Header.jsx`, `Home.jsx`, `Explore.jsx`, `ShopPage.tsx`, `MenShop.jsx`, `WomenShop.jsx`, `KidsShop.jsx`, `SavedLooks.jsx`, `ProfilePage.tsx`.
- **Avatar Pages:** Added `ConsumerAvatarViewport.tsx`, `AvatarLandingPage.tsx`, `AvatarCreateWizard.tsx`, `AvatarDashboardPage.tsx`.
- **Admin UI:** Added `src/api/admin.ts`, `src/components/admin/AdminLayout.tsx`, `src/pages/admin/AdminDashboardPage.tsx`, updated `Login.jsx` & `SellerRegisterInfoPage.tsx`.
- **3D Cloth Simulation & Try-On:** Updated `AnatomicalCollider.ts`, `WeldedClothSolver.ts`, `clothWorker.ts`, `WorkerClothClient.ts`, `ExperimentalTryOnPage.tsx`, `src/api/client.ts`.
- **Proxy (`frontend/vite.config.js`):** Added `/api/admin` proxy rule to `:8001`.

---

## 22. Testing Results

All checks below ran cleanly after their corresponding implementation edits:

| Suite | Command | Result | Scope & Notes |
| :--- | :--- | :---: | :--- |
| **Frontend Unit & Component Suite** | `cd frontend; npm test -- --run` | **9 files / 30 tests passed** (`3.29s`) | Ran after final edit; covers `WeldedClothSolver`, `api_client`, `auth_context`, `Phase13CustomerAdminExperience`, `Phase13PortalSeparation`, `Phase12Marketplace`, `honest_fit_display`, `SimplifiedUX`, `AvatarViewer` |
| **Frontend Typecheck & Production Build** | `cd frontend; npm run build` (`tsc --noEmit && vite build`) | **Passed** (`0` TS errors, `1.00s`) | Ran after final edit; bundles Web Worker (`clothWorker-*.js`) cleanly |
| **Commerce Backend Tests** | `cd backend; pytest tests/test_dual_mode_marketplace_p12.py tests/test_rbac_portals_p13.py tests/test_admin_portal_p13.py -v` | **9 passed** (`88.36s`) | Dual-mode capabilities, RBAC login/privilege isolation, admin governance & seller rejection/approval lifecycle |
| **Body Engine Avatar & API Tests** | `cd WEARWISE-BODY-ENGINE; pytest tests/avatar_engine tests/api/test_phase13_body_engine_rbac.py tests/api/test_api_workflow.py tests/api/test_merchant_lifecycle_m4_m5b.py -v` | **35 passed** (`173.47s`) | Includes 9 closed-loop avatar accuracy tests (`<= 1.6 cm`), rigged centering/grounding, shopper published binary vs private merchant 403 isolation, workflow & staging isolation |
| **Live Browser E2E (Playwright)** | `phase13_e2e_verify.py` against `:8000`, `:8001`, `:4173` | **All 7 checks PASS** (`page_errors: []`) | Desktop `1440x900` & Mobile `390x844`, zero telemetry leaks on customer pages, 0 HTTP 403/422 errors during avatar creation, GLB fetch, or 3D try-on |

---

## 23. Regression Results

- Protected reference asset checksums verified unchanged:
  - `graded_m2rc/S/*.glb`: `8F9BD0C79C54D4F40E3354F729C5F236634ACEC3A06D33A1F0EC771B51E41690`
  - `graded_m2rc/M/*.glb`: `9B6212FF218BA6231000CDCA1716F808FD501DF4E843353655EC7CE4D7389769`
  - `graded_m2rc/L/*.glb`: `4BC1A0CBCB0CCCBE3B4BD5646B614BC881A06D5DB06EC44B0034A577E8101387`
- `Phase12Marketplace.test.tsx`, `Phase13PortalSeparation.test.tsx`, `test_dual_mode_marketplace_p12.py`, `test_api_workflow.py`, and `test_merchant_lifecycle_m4_m5b.py` all continue passing.

---

## 24. Known Issues

1. **Guest `/api/auth/me` `401` Console Log:** Unauthenticated visits trigger one initial `401` check on `/api/auth/me` from `StoreAuthContext` before settling cleanly into guest state (functional behavior unaffected).
2. **Stale Pytest Staging Product Image `404`:** A residual test catalog entry (`TSH-WW-PYTEST-78FC99`) referenced a deleted image path in staging logs (`404 Not Found`), while all `17` core catalog products and valid merchant assets load cleanly.
3. **Extreme Pose + Cross-Shape Shirt Fit:** Slight lower-left hip hem clipping and overhead stretch stripes remain visible on `P3 Arms Overhead` when draping a male CAD Size M tee onto a `165 cm / 108 cm hip` Hourglass mannequin.
4. **Windows Host PyTorch Note:** On-the-fly Anny generation runs cleanly inside `WEARWISE-BODY-ENGINE/.venv-anny`; hosts missing AppLocker/DLL clearance for PyTorch remain protected by lazy adapter loading.

---

## 25. Future Work

- Parametric / body-shape-graded garment scaling or custom pattern blocks per customer archetype (`feminine` / `masculine` blocks) so `TSH-WW-*` garments match Hourglass/Curvy hip ease cleanly.
- Connect a production VTON provider (`FASHN_API_KEY` or `VTON_API_URL`) to enable Photo Try-On alongside 3D Fitting Room.
- Replace simulated staging checkout with a real payment provider webhook & signature flow.
- Clean up stale pytest-generated sample product artifacts (`TSH-WW-PYTEST-*`) from staging catalogs during CI teardown.

---

## 26. Deployment Readiness

- **Staging Status:** Ready for interactive staging demos and academic/product evaluation across Customer, Seller, and Admin flows.
- **Production Status:** Requires setting `WEARWISE_ENV=production`, `ALLOW_DEV_AUTH=false`, strong `JWT_SECRET_KEY`, strict `CORS_ALLOWED_ORIGINS`, MongoDB production indexes, real payment gateway integration, and external VTON credentials if Image Try-On is enabled.

---

## 27. Exact Commands for Running the Application

Run in three separate PowerShell terminals from the repository root (`c:\Users\Lenovo\Documents\Major Project\WearWise`):

1. **Body & Garment Engine (`:8000`):**
```powershell
Set-Location WEARWISE-BODY-ENGINE
$env:MONGODB_BODY_ENGINE_DB = "wearwise_body_engine_staging"
$env:MONGODB_COMMERCE_DB = "wearwise_commerce_staging"
.\.venv-anny\Scripts\python.exe -m uvicorn app.api.app:app --host 127.0.0.1 --port 8000
```

2. **Commerce & Admin API (`:8001`):**
```powershell
Set-Location backend
$env:MONGODB_COMMERCE_DB = "wearwise_commerce_staging"
$env:MONGODB_BODY_ENGINE_DB = "wearwise_body_engine_staging"
$env:WEARWISE_DEV_ADMIN_PASSWORD = "123456"
..\WEARWISE-BODY-ENGINE\.venv-anny\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

3. **Frontend Dev or Preview (`:5173` / `:4173`):**
```powershell
Set-Location frontend
npm run dev
# Or production bundle preview:
# npm run build; npx vite preview --host 127.0.0.1 --port 4173
```

---

## 28. Development Login Credentials

Provisioned exclusively for local/staging development (see `backend/scripts/seed_admin.py` and `backend/app/core/security.py`):

| Portal Role | Login Route | Email | Password |
| :--- | :--- | :--- | :--- |
| **Customer** | `/login` | `shopper@wearwise.test` | `$SEED_SHOPPER_PASSWORD` (dev fallback: `WearWiseShopper#2026`) |
| **Approved Seller** | `/seller/login` | `seller@wearwise.studio` | `$SEED_SELLER_PASSWORD` (dev fallback: `WearWiseSeller#2026`) |
| **Pending Seller** | `/seller/login` (blocked until approved) | `pending.seller@wearwise.studio` | `$SEED_PENDING_SELLER_PASSWORD` (dev fallback: `WearWisePending#2026`) |
| **Platform Admin** | `/admin/login` | `admin@wearwise.com` | `$WEARWISE_DEV_ADMIN_PASSWORD` (dev default in staging script: `123456`) |

---

## 29. Implemented vs. Experimental Features

| Feature Area | Classification | Notes |
| :--- | :--- | :--- |
| **3-Role Auth, RBAC, CSRF, Cookie Sessions** | Genuinely Implemented | Server-authoritative roles, revocation & admin routes verified by pytest & Playwright |
| **Customer Storefront, Shop (`/shop/*`), Cart, Wishlist, Orders** | Genuinely Implemented | Real catalog & persistence (`Simulated staging checkout` noted honestly on orders) |
| **Seller Approval Lifecycle & Admin Portal (`/admin`)** | Genuinely Implemented | Full CRUD, seller approval/rejection/reapplication, product/customer moderation, audit logs |
| **Anny Avatar Synthesis & Anthropometry Calibration** | Genuinely Implemented | Closed-loop 3D generation with `<= 1.6 cm` measured accuracy across male/female presets |
| **Real-Time 3D Cloth Simulation & Fit Tension Heatmap** | Implemented (Simulation Estimate) | Live Web Worker XPBD cloth + anatomical collision + edge-stretch heatmap; physics/material strain values are simulated mesh estimates rather than laboratory tensile tests |
| **AI Recommendations & Image VTON** | Honest Fallback / External Key Pending | `/explore` uses honest catalog/category curation; `/image-try-on` fails closed with `503` until `FASHN_API_KEY` or `VTON_API_URL` is provided |

---

## 30. Verified Live Browser Captures

Captured via automated headless Chromium (`Playwright`, Desktop `1440x900` and Mobile `390x844`) against live staging servers (`:8000`, `:8001`, `:4173`) in `C:\Users\Lenovo\.gemini\antigravity\brain\1b991b5d-20b1-4e85-8a22-a6d0563d38e8\scratch\screenshots\`:

- `01_home_desktop.png` — Consumer marketplace homepage with clean 8-item nav bar and Women/Men/Kids collections.
- `02_avatar_step2_3d.png` — Step 2 initial 3D avatar preview showing live Hourglass `165 cm` feminine mannequin.
- `03_avatar_dashboard.png` — Saved Avatar Studio showing live 3D preview + extracted measurements (`Chest 89 cm`, `Waist 63 cm`, `Hips 108 cm`, `Shoulders 40 cm`) and 3D-ready catalog items.
- `04_tryon_strain_heatmap.png` — Virtual Fitting Room in `P3 Arms Overhead` with live `Fit Tension Heatmap`, `Size S` recommendation, and `Overall Feel: Snug`.
- `05_mobile_nav.png` — Mobile (`390x844`) layout with zero horizontal overflow and responsive 2x4 drawer.
- `06_seller_dashboard.png` — Isolated Seller Portal workspace shell (`WearWise Official Studio`).
- `07_admin_overview.png` — Admin Platform Administration dashboard with live KPI cards and pending seller `Approve` / `Reject...` workflow.
