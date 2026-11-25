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

## 2. Authentication, Ownership & Environment Isolation

- **Merchant Endpoints (`/api/v1/merchant/garments/*`):** Enforce `get_current_brand_id` ownership checks across reads, private images, private GLBs, edits, approvals, publishes, and rollbacks (`403` cross-brand).
- **Production Auth Boundary:** When `WEARWISE_ENV=production` / `APP_ENV=production`, dev header impersonation (`ALLOW_DEV_AUTH`) is disabled and signed JWT Bearer verification is strictly enforced (`test_auth_security.py`).
- **Database Isolation:** All staging servers and automated tests set `MONGODB_BODY_ENGINE_DB=wearwise_body_engine_staging` and `MONGODB_COMMERCE_DB=wearwise_commerce_staging` so production databases remain untouched.
- **Secret Hygiene:** Real API keys (`FASHN_API_KEY`, `VTON_API_KEY`, `MONGODB_URI`, `JWT_SECRET_KEY`) live only in environment variables or `.env` (gitignored); `.env.example` contains variable templates only.
