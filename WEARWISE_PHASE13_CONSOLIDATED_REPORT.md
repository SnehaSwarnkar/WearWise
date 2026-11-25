# WEARWISE — PHASE 13 CONSOLIDATED ENGINEERING REPORT

**Phase:** 13 — Separate Shopper & Seller Portals, Authentication & Role-Based Access Control  
**Date:** 2026-11-25  
**Environment:** Staging only (`wearwise_commerce_staging`, `wearwise_body_engine_staging`) — **Production untouched**  
**Branch:** `remediation/m2r-a-pattern-prototype`

---

## 1. Part 1 — Existing Authentication Architecture Assessment

Before Phase 13 changes, inspection of `backend/`, `WEARWISE-BODY-ENGINE/`, and `frontend/` identified four key gaps:
1. **No Server Roles or Seller Approval State:** `wearwise_commerce_staging.users` stored only unsalted SHA-256 `password_hash`, `name`, `email`, and shopper onboarding flags (`gender`, `bodyType`, `onboardingDone`) with zero `role`, `status`, `seller_approved`, or `brand_id` fields. Tokens were deterministic `sha256("wearwise-" + user_id)` values stored in `localStorage` (`ww-auth-token`) with no expiry or server-side logout revocation.
2. **Client-Side Dev Role Toggle & Open Merchant Routes:** `Header.jsx` and `BodyEngineAuthContext.tsx` exposed a client-side `SHOPPER / MERCHANT` toggle (`switchRole('brand')`) plus direct `Digital Garment Studio` links inside the shopper navbar, while `frontend/src/api/merchantGarments.js` sent zero authentication headers (`ALLOW_DEV_AUTH` silently defaulted anonymous callers to `DEFAULT_DEV_BRAND_ID`).
3. **Unseparated Shopper/Seller Endpoints:** Commerce `orders.py`, `wardrobe.py`, `saved.py`, `avatar.py`, and `assistant.py` performed no role verification, and Commerce exposed no seller-scoped dashboard, product CRUD, inventory, or seller order endpoints.
4. **Shared Database Readiness:** Both `backend/` and `WEARWISE-BODY-ENGINE/` already share the same MongoDB Atlas `MONGODB_URI`, `MONGODB_COMMERCE_DB`, and PyJWT `HS256` key configuration (`wearwise:auth` / `wearwise:api`), enabling unified cross-service RBAC without creating a duplicate auth database.

---

## 2. Implemented & Verified Phase 13 Architecture

| Deliverable | Status | Implementation Highlights |
| :--- | :--- | :--- |
| **Authoritative Account Roles & Safe Migration** | **Implemented & Tested** | Server-side roles `shopper`, `seller`, `admin` and statuses `active`, `pending`, `suspended` implemented in [security.py](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/backend/app/core/security.py). Existing legacy accounts automatically resolve/migrate to active `shopper` while preserving IDs, onboarding, and orders; approved staging sellers, pending applicant, staging shopper, and admin accounts are idempotently seeded on startup (`APP_ENV != production`). |
| **HTTP-Only Cookie Sessions, CSRF & Revocation** | **Implemented & Tested** | Salted PBKDF2-HMAC-SHA256 (`pbkdf2_sha256$...`) password hashing (with safe backward-compat verification for legacy M5 test accounts), signed `HS256` JWT stored in HTTP-only `ww_auth_session` cookie + `ww_csrf_token` double-submit CSRF validation (`X-CSRF-Token`), zero auth secrets in `localStorage`, and server-side session `jti` revocation in `auth_sessions` on `POST /api/auth/logout`. |
| **Dual-Portal Auth Entry Experience (`/auth`)** | **Implemented & Tested** | [AuthLandingPage.tsx](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/pages/AuthLandingPage.tsx) presents distinct **SHOPPER LOGIN** (`"Discover fashion, find your fit and shop with WearWise."`) and **SELLER LOGIN** (`"Manage your products, publish garments and grow your store."`) cards in WearWise editorial cream/black/pink/lime/purple styling. |
| **Role-Specific Login Enforcement** | **Implemented & Tested** | `POST /api/auth/login` (`/login`) rejects sellers with `"This is a seller account. Please use Seller Login."`; `POST /api/auth/seller/login` (`/seller/login`) rejects shoppers with `"This account is registered as a shopper. Please use Shopper Login or contact WearWise about seller access."` and blocks unapproved/pending/suspended sellers (`403`). Public signup (`/register`, `/signup`) strictly enforces `role="shopper"`; `/seller/register` (`POST /api/auth/seller/apply`) submits non-privileged pending requests requiring WearWise admin approval (`POST/PATCH /api/auth/admin/sellers`). |
| **Separate Shopper Portal & Header** | **Implemented & Tested** | Removed `SHOPPER/MERCHANT` dev toggle and `[MERCHANT]` studio links from [Header.jsx](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/pages/Header.jsx); shopper-protected routes wrapped in `ShopperRoute` inside [App.tsx](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/App.tsx) while preserving `/explore`, `/product/:sku`, `/experimental-try-on`, `/image-try-on`, `/try-on`, `/cart`, `/checkout`, and `/order-confirmation`. |
| **Separate Seller Portal (`/seller/*`)** | **Implemented & Tested** | Built [SellerLayout.tsx](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/components/seller/SellerLayout.tsx), [SellerDashboardPage.tsx](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/pages/seller/SellerDashboardPage.tsx), [SellerProductsPage.tsx](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/pages/seller/SellerProductsPage.tsx) (`/products`, `/products/new`, `/inventory`), [SellerOrdersPage.tsx](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/pages/seller/SellerOrdersPage.tsx), [SellerStudioPage.tsx](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/pages/seller/SellerStudioPage.tsx) (`MerchantGarmentStudio embedded`), and [SellerProfilePage.tsx](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/pages/seller/SellerProfilePage.tsx), backed strictly by `/api/seller/*` (`require_active_seller`) and `brand_id` ownership checks. |
| **Cross-Service Body Engine RBAC** | **Implemented & Tested** | [auth.py](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/app/api/auth.py) validates HTTP-only `ww_auth_session` cookies + CSRF + Bearer JWTs against shared `auth_sessions` & active/approved `users`, rejects anonymous unauthenticated `/api/v1/merchant/garments` calls (`401`), rejects shoppers (`403`), and passes cookies seamlessly via [vite.config.js](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/vite.config.js) proxy & [merchantGarments.js](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/api/merchantGarments.js). |
| **Lazy PyTorch / Anny Boot Resilience** | **Implemented & Tested** | Made `torch` and `anny` lazy in [vton_provider.py](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/app/services/vton_provider.py), [anny_adapter.py](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/app/avatar_engine/adapters/anny_adapter.py), and [avatar_service.py](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/WEARWISE-BODY-ENGINE/app/services/avatar_service.py) so Body Engine `:8000` boots cleanly even when Windows Application Control blocks unsigned `torch_python.dll`. |

### Deferred / Honest Environment Boundaries
- **On-the-Fly Local PyTorch Anny Generation (`POST /api/v1/avatar/generate`):** Blocked on this Windows host by OS Application Control (`OSError: [WinError 4551]` on unsigned `torch_python.dll` inside `.venv-anny`); pre-calibrated `PROFILE_A..E.glb` avatars and Rev3 garments on `/experimental-try-on` and `/try-on` continue operating normally.
- **External AI VTON Image Synthesis:** Still intentionally fail-closed (`503 PROVIDER_UNAVAILABLE`) until an external credential (`FASHN_API_KEY` or `VTON_API_URL`) is supplied.
- **Self-Serve Admin Portal UI:** Seller approval/suspension endpoints (`GET/POST/PATCH /api/auth/admin/sellers`) are implemented and tested via API; a standalone frontend admin console UI is deferred.

---

## 3. Verification Evidence & Test Results

| Verification Check | Command & Scope | Exact Observed Result |
| :--- | :--- | :--- |
| **Commerce Backend & RBAC Suite** | `pytest backend/tests -v` (`test_commerce_m5.py`, `test_dual_mode_marketplace_p12.py`, `test_rbac_portals_p13.py`) | **`10 passed` in `13.43s`** |
| **Body Engine RBAC, VTON, Security & Lifecycle Suite** | `pytest tests/api/test_phase13_body_engine_rbac.py tests/api/test_phase12_vton_and_capabilities.py tests/api/test_auth_security.py tests/api/test_merchant_lifecycle_m4_m5b.py -v` | **`16 passed` in `27.63s`** |
| **Body Engine Non-PyTorch Regression Suite** | `pytest tests -q --ignore=tests/avatar_engine --ignore=tests/api/test_api_workflow.py --ignore=tests/test_{export,mesh_validity,model_generation,parameter_changes}.py` | **`375 passed`, `9` collection/setup errors strictly on `test_real_extraction.py` due to Windows OS `[WinError 4551]` on `torch_python.dll`** (`49.10s`) |
| **Frontend Vitest Unit & Portal Separation Tests** | `npm test -- --run` across `8` test files (`Phase13PortalSeparation.test.tsx`, `Phase12Marketplace.test.tsx`, `SimplifiedUX.test.tsx`, `auth_context.test.tsx`, `api_client.test.ts`, `AvatarViewer.test.tsx`, `WeldedClothSolver.test.ts`, `honest_fit_display.test.tsx`) | **`8` test files passed, `26` tests passed** (`1.93s`) |
| **Frontend Production Bundle** | `npm run build` (`tsc --noEmit && vite build`) | **Passed (`0` errors, `609ms`)** |
| **Desktop & Mobile Playwright E2E** | Headless Chromium (`1440x900` & `390x844`) against `uvicorn :8010`, `uvicorn :8011`, `vite preview :4175` | **`E2E_PHASE13_PASSED PAGE_ERRORS=0`** (`10` verified screenshots saved in `artifacts/phase13/`, mobile scroll overflow `<= 2px`, 3D Try-On `Cherry Baby Tee` verified without load error) |
| **Protected Rev3 Baseline Checksums** | SHA-256 verification on `graded_m2rc/{S,M,L}/TSH-WW-CREW-001_*_rev3.glb` | **`L`: `4BC1A0...387`, `M`: `9B6212...769`, `S`: `8F9BD0...690` (unchanged)** |

---

## 4. Updated Documentation & Visual Evidence

- Updated [docs/SECURITY_AND_PRIVACY.md](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/docs/SECURITY_AND_PRIVACY.md) and [docs/DEVELOPMENT.md](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/docs/DEVELOPMENT.md) with Phase 13 RBAC, HTTP-only cookie + CSRF design, Vite proxy routing, and staging portal credentials (`shopper@wearwise.test`, `seller@wearwise.studio`, `studio.two@wearwise.studio`, `pending.seller@wearwise.studio`).
- Desktop and mobile verification screenshots archived in `artifacts/phase13/` (`01_auth_landing_desktop.png` through `10_auth_landing_mobile.png`).
