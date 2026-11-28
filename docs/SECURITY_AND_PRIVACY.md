# WearWise Security & Photo Privacy Policy

## 1. Image Virtual Try-On Privacy Controls

Implemented across `PersonImageService`, `VTONJobService`, `HonestVTONProviderAdapter`, and `/api/v1/try-on/vton`:

1. **Explicit User Consent (`consent=true`):** Requests missing affirmative opt-in consent are rejected (`HTTP 422`) before image processing or storage.
2. **Strict Input Validation:** Enforces JPEG/PNG/WebP format verification via Pillow, `10 KB – 10 MB` byte limits, minimum `256×256` dimensions, EXIF orientation normalization, and synthetic-avatar rejection.
3. **EXIF & Device Metadata Stripping:** Decoded pixels are copied onto a clean RGB `Image.new("RGB", ...)` surface before re-encoding, removing camera, GPS, and device EXIF blocks.
4. **No Silent Upload Retention When Provider Unavailable:** If no external AI VTON provider is configured or healthy, any validated temporary upload is deleted immediately and the API fails closed with `503 PROVIDER_UNAVAILABLE`.
5. **Automatic Temp Cleanup & On-Demand Deletion:** Raw customer photographs are deleted automatically in the job pipeline `finally` block (`temp_upload_deleted=True`), and shoppers can delete jobs and generated outputs at any time (`DELETE /api/v1/try-on/vton/jobs/{job_id}`).
6. **Owner-Scoped Access & Non-Cacheable Delivery:** `GET /jobs/{id}`, `GET /jobs/{id}/results`, `DELETE /jobs/{id}`, and `GET /images/{filename}` verify `job["user_id"] == user_id` (`403` otherwise), block direct access to `person_*` raw upload names (`403`), and set `Cache-Control: private, no-store`.
7. **No Model Training:** Neither WearWise nor recommended commercial APIs (FASHN AI API / Google Vertex AI) use uploaded customer photographs for model training.

---

## 2. Role-Based Access Control, Sessions & Environment Isolation

- **Server-Authoritative Roles (`shopper`, `seller`, `admin`):** Roles, active status, `seller_approved` flags, and seller `brand_id` ownership live strictly in the server database (`wearwise_commerce_staging.users`). Public shopper signup (`/api/auth/signup`, `/api/auth/register`) always assigns `role="shopper"` and strips client privilege fields.
- **Role-Separated Portal Login:** `/api/auth/login` rejects `seller` accounts cleanly (`403`), `/api/auth/seller/login` rejects `shopper`, `pending`, and `suspended` accounts cleanly (`403`), and sellers are provisioned/approved exclusively via WearWise admin workflows (`/api/auth/admin/sellers`).
- **HTTP-Only Cookie Sessions, Revocation & CSRF Protection:** Authentication mints signed HS256 JWTs (`iss="wearwise:auth"`, `aud="wearwise:api"`, unique `jti`) stored in an HTTP-only `ww_auth_session` cookie (never `localStorage`) with a `ww_csrf_token` double-submit CSRF check (`X-CSRF-Token`) on cookie-authenticated mutations. `POST /api/auth/logout` revokes `jti` server-side across both Commerce (`:8001`) and Body Engine (`:8000`) via shared `auth_sessions`.
- **Merchant Endpoints (`/api/seller/*` & `/api/v1/merchant/garments/*`):** Enforce `require_active_seller` / `get_current_brand_id` ownership checks across reads, private images, private GLBs, edits, approvals, publishes, orders, and rollbacks (`401` unauthenticated, `403` shopper or cross-seller).
- **Shopper-Only Portal Guards:** Authenticated sellers are blocked (`403`) from shopper-only endpoints (`/api/orders/my`, `/api/wardrobe/*`, `/api/saved/*`, `/api/avatar/*`, `/api/assistant/*`, and customer review creation).
- **Production Auth Boundary:** When `WEARWISE_ENV=production` / `APP_ENV=production`, dev header impersonation (`ALLOW_DEV_AUTH`) is disabled and signed JWT verification is strictly enforced (`test_auth_security.py`).
- **Database Isolation:** All staging servers and automated tests set `MONGODB_BODY_ENGINE_DB=wearwise_body_engine_staging` and `MONGODB_COMMERCE_DB=wearwise_commerce_staging` so production databases remain untouched.
- **Secret Hygiene:** Real API keys (`FASHN_API_KEY`, `VTON_API_KEY`, `MONGODB_URI`, `JWT_SECRET_KEY`) live only in environment variables or `.env` (gitignored); `.env.example` contains variable templates only.
