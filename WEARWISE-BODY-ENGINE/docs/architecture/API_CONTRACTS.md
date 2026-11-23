# WearWise REST API Contract & Transport Specification

**Project:** WearWise AI Fashion & Honest Fit Platform  
**Document:** API Contracts Specification (API-001)  
**Revision:** 1.1 (Authenticated Ownership, Private GLB Delivery & Complete Catalog)  
**Date:** 2026-11-23  
**Status:** Approved Technical Architecture  

---

## 1. Architectural Standards & Authentication Security

- **Base Path:** `/api/v1`.
- **Authentication & Ownership Boundary:**
  - Clients must authenticate via standard Bearer Token (`Authorization: Bearer <token>`) or authenticated session cookie.
  - Profile ownership is derived **strictly from the authenticated principal** (`request.state.current_user_id`).
  - Request payloads must **never accept `user_id` as a client-supplied field**. Any attempt to read or modify a profile belonging to another principal returns `403 Forbidden` (or `404 Not Found` to prevent profile enumeration).
- **GLB Privacy & Caching Policy:**
  - 3D avatar files represent personal physical data. Shared public CDN caching is **strictly forbidden**.
  - All GLB endpoints require user authorization and return:
    `Cache-Control: private, max-age=86400, immutable`
    `ETag: "<sha256_content_checksum>"`
- **Concurrency & Idempotency:**
  - State-modifying endpoints (`POST /avatar/generate`, `POST /profiles/{id}/measurements`) require an `Idempotency-Key: <UUID>` header.
  - Concurrent profile updates use optimistic locking via `expected_revision_number`. If a race condition occurs, the server returns `409 Conflict`.

---

## 2. Standard Error Envelope

Every $4xx$ and $5xx$ error returns a structured, machine-readable envelope:

```json
{
  "error": {
    "code": "MEASUREMENT_OUT_OF_BOUNDS",
    "message": "Waist planar circumference (165.0 cm) exceeds safe anatomical bounds.",
    "status_code": 422,
    "timestamp": "2026-11-23T11:45:00.123456Z",
    "details": [
      {
        "field": "measurements[0].value_cm",
        "issue": "Value must be between 40.0 and 160.0 cm."
      }
    ]
  }
}
```

---

## 3. Complete Endpoint Catalogue

### 3.1 Body Profiles (`/api/v1/profiles`)

#### `POST /api/v1/profiles` — Create Body Profile
- **Auth:** Required (Ownership set to `current_user_id`).
- **Request:**
```json
{
  "presentation_gender": "masculine",
  "stature_cm": 178.50,
  "reported_weight_kg": 74.00,
  "initial_controls": {
    "shoulder_width": 0.55,
    "chest_fullness": 0.50,
    "belly_fullness": 0.45,
    "waist_definition": 0.60
  }
}
```
- **Response (201 Created):**
```json
{
  "profile_id": "c1f7a28e-8e3b-48d9-a791-03f4439c1b3e",
  "current_revision": 1,
  "presentation_gender": "masculine",
  "stature_cm": 178.50,
  "reported_weight_kg": 74.00,
  "current_avatar_id": null,
  "created_at": "2026-11-23T11:00:00Z",
  "updated_at": "2026-11-23T11:00:00Z"
}
```

#### `GET /api/v1/profiles/{profile_id}` — Retrieve Body Profile
- **Auth:** Required (Must own `profile_id`).
- **Response (200 OK):** Returns active profile summary, active measurements, controls, and latest avatar asset URL.

#### `PATCH /api/v1/profiles/{profile_id}` — Update Profile Metadata
- **Auth:** Required.
- **Request:** `{"presentation_gender": "neutral", "reported_weight_kg": 73.5}`.
- **Response (200 OK):** Updated profile record.

#### `GET /api/v1/profiles/{profile_id}/revisions` — Retrieve Revision History
- **Auth:** Required.
- **Response (200 OK):** List of past profile revisions with timestamps and change summaries.

---

### 3.2 Measurements (`/api/v1/profiles/{profile_id}/measurements`)

#### `POST /api/v1/profiles/{profile_id}/measurements` — Record Measurements
Appends a new immutable profile revision with the updated measurements.
- **Headers:** `Idempotency-Key: <UUID>`
- **Request:**
```json
{
  "expected_revision": 1,
  "measurements": [
    {
      "measurement_code": "chest_circumference",
      "value_cm": 104.50,
      "unit": "cm",
      "acquisition_method": "tape_measured",
      "tolerance_cm": 1.00,
      "landmark_convention": "bust_nipple_apex_72pct"
    },
    {
      "measurement_code": "waist_planar_circumference",
      "value_cm": 84.00,
      "unit": "cm",
      "acquisition_method": "tape_measured",
      "tolerance_cm": 1.00,
      "landmark_convention": "planar_horizontal_natural_waist"
    }
  ]
}
```
- **Response (200 OK):**
```json
{
  "profile_id": "c1f7a28e-8e3b-48d9-a791-03f4439c1b3e",
  "new_revision": 2,
  "recorded_count": 2,
  "active_measurements": {
    "stature": {"value_cm": 178.50, "acquisition_method": "user_reported", "validation_state": "internally_consistent"},
    "chest_circumference": {"value_cm": 104.50, "acquisition_method": "tape_measured", "validation_state": "internally_consistent"},
    "waist_planar_circumference": {"value_cm": 84.00, "acquisition_method": "tape_measured", "validation_state": "internally_consistent"}
  }
}
```

---

### 3.3 Semantic Body Controls (`/api/v1/profiles/{profile_id}/controls`)

#### `GET /api/v1/controls/definitions` — Retrieve Supported Controls
- **Response (200 OK):** Catalog of semantic controls, defaults, display names, and safe ranges.

#### `PUT /api/v1/profiles/{profile_id}/controls` — Update Semantic Controls
- **Request:**
```json
{
  "expected_revision": 2,
  "controls": {
    "shoulder_width": 0.65,
    "chest_fullness": 0.50,
    "belly_fullness": 0.40,
    "waist_definition": 0.70,
    "arm_fullness": 0.60,
    "hip_fullness": 0.50,
    "thigh_fullness": 0.55,
    "calf_fullness": 0.50
  }
}
```
- **Response (200 OK):** Returns new revision number (`3`) and flags `is_avatar_stale: true`.

---

### 3.4 Avatar Generation & Asset Delivery (`/api/v1/avatar`)

#### `POST /api/v1/avatar/generate` — Generate 3D Avatar
Invokes `AvatarOrchestrationService` synchronously (target latency $<150\text{ ms}$).
- **Headers:** `Idempotency-Key: <UUID>`
- **Request:** `{"profile_id": "c1f7a28e-8e3b-48d9-a791-03f4439c1b3e"}`
- **Response (200 OK):**
```json
{
  "avatar_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "profile_id": "c1f7a28e-8e3b-48d9-a791-03f4439c1b3e",
  "profile_revision": 3,
  "asset_url": "/api/v1/avatar/assets/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d.glb",
  "format": "glb",
  "size_bytes": 483244,
  "sha256_checksum": "a8f5c3b18d7e2194e9f731c261e4a11f262175a2d614d9b04f762692e8617822",
  "generation_duration_ms": 28.40,
  "extracted_measurements": {
    "stature": 178.50,
    "chest_circumference": 104.48,
    "waist_planar_circumference": 83.92,
    "shoulder_biacromial_breadth": 41.20
  }
}
```

#### `GET /api/v1/avatar/{avatar_id}/status` — Retrieve Generation Status & Metadata
- **Response (200 OK):** Returns validation health, vertex count, face count, and engine metadata.

#### `GET /api/v1/avatar/assets/{avatar_id}.glb` — Stream Private Binary GLB
- **Auth:** Required (Verified profile owner).
- **Headers Returned:**
  - `Content-Type: model/gltf-binary`
  - `Cache-Control: private, max-age=86400, immutable`
  - `ETag: "a8f5c3b18d7e2194e9f731c261e4a11f262175a2d614d9b04f762692e8617822"`
- **Response:** Raw binary glTF 2.0 payload.

---

### 3.5 Garment Management (`/api/v1/garments`)

#### `POST /api/v1/garments` — Create Garment Profile
- **Request:**
```json
{
  "brand_id": "d3b07384-d113-49d6-bb4d-6218f0896088",
  "sku": "TSH-CREW-001",
  "title": "Heavyweight Classic Crewneck",
  "category": "t_shirt",
  "fabric_properties": {
    "fibre_composition": {"cotton": 1.0},
    "mechanical_stretch_pct": 0.05,
    "stretch_recovery_pct": 0.90,
    "stretch_direction": "rigid_zero"
  }
}
```
- **Response (201 Created):** Created garment profile record.

#### `POST /api/v1/garments/{garment_id}/sizes` — Add Size Specifications
- **Request:**
```json
{
  "size_label": "L",
  "sort_order": 3,
  "measurements": [
    {"dimension_code": "garment_chest_circumference", "value_cm": 112.00, "tolerance_cm": 1.00},
    {"dimension_code": "garment_shoulder_seam_width", "value_cm": 44.50, "tolerance_cm": 1.00},
    {"dimension_code": "garment_back_length", "value_cm": 74.00, "tolerance_cm": 1.00}
  ]
}
```

#### `GET /api/v1/garments/{garment_id}` — Retrieve Garment Specification & Size Table
- **Response (200 OK):** Complete garment details with dimensions for all sizes.

---

### 3.6 Honest Fit Recommendation (`/api/v1/fit`)

#### `POST /api/v1/fit/recommend` — Request Sizing Recommendation
- **Request:**
```json
{
  "profile_id": "c1f7a28e-8e3b-48d9-a791-03f4439c1b3e",
  "garment_id": "e4d9b2a1-5f3c-4b8a-9e1d-8f7a6b5c4d3e",
  "user_fit_preference": "regular"
}
```
- **Response (200 OK):**
```json
{
  "recommendation_id": "7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d",
  "garment_id": "e4d9b2a1-5f3c-4b8a-9e1d-8f7a6b5c4d3e",
  "recommended_size": "L",
  "composite_fit_score": 94.5,
  "status": "ready",
  "alternative_size": {
    "size_label": "M",
    "fit_summary": "Tailored / Fitted silhouette"
  },
  "regional_comparisons": [
    {
      "region": "chest",
      "body_measurement_cm": 104.50,
      "garment_dimension_cm": 112.00,
      "ease_cm": 7.50,
      "classification": "regular",
      "explanation": "Standard comfortable room (+7.5 cm ease)."
    },
    {
      "region": "shoulder",
      "body_measurement_cm": 41.20,
      "garment_dimension_cm": 44.50,
      "ease_cm": 3.30,
      "classification": "regular",
      "explanation": "Shoulder seams align naturally with your acromion."
    }
  ],
  "disclaimer": "Ease thresholds are provisional baselines pending Phase 5 physical wear trials."
}
```

---

## 4. Frontend Compatibility & Legacy Mapping

The existing React frontend calls legacy endpoints:
1. `POST /api/avatar/save` $\rightarrow$ Mapped via FastAPI router shim to `POST /api/v1/profiles` (creating profile and saving controls).
2. `GET /api/avatar/{session_id}` $\rightarrow$ Mapped to `GET /api/v1/profiles/{profile_id}`.
3. 3D GLB Loading: Frontend Three.js canvas consumes `/api/v1/avatar/assets/{avatar_id}.glb` directly via standard `GLTFLoader` with `credentials: 'include'`.
