# WearWise System Architecture & Component Specification

**Project:** WearWise AI Fashion & Honest Fit Platform  
**Document:** System Architecture Specification (SAS-001)  
**Revision:** 1.2.1 (Engine-Isolated Modular Monolith, Evaluation Port & Atomic Storage Safety)  
**Date:** 2026-11-23  
**Status:** Approved Technical Architecture  

---

## 1. Context and Architectural Goals

WearWise is an AI fashion and honest-fit intelligence platform designed to eliminate apparel sizing uncertainty by providing measurement-grounded 3D avatars and transparent garment ease calculations without requiring photographs, body scans, or mobile depth sensors.

### Architectural Constraints & Invariants:
1. **Python Modular Monolith (FastAPI):** A single unified deployable backend process with strictly decoupled internal module boundaries. No microservices, distributed message brokers, or Kubernetes orchestration are permitted at this stage.
2. **Strict Unidirectional Dependency Direction:** API routers invoke application-level services. Low-level domain engines (Avatar Engine, Anthropometry, BICE, Fit Engine) never orchestrate higher-level modules or each other.
3. **Engine-Neutral Avatar Generation & Evaluation:** NAVER Anny v0.6.2 is encapsulated completely behind abstract engine interfaces in `app/avatar_engine/adapters/anny_adapter.py`. BICE consumes `ShapeEvaluationPort` and outputs `AvatarShapeSpec`. Anthropometry consumes `MeshData` and `LandmarkProvider`.
4. **Local Hardware Budget Compliance (₹0 Mandate):** Real-time interactive avatar previews run on CPU PyTorch tensors ($20.82\text{ ms}$ model latency on an AMD Ryzen 7 6800H), achieving ₹0 infrastructure viability.
5. **Frontend Preservation:** The existing frontend is a decoupled React 19 + Vite application. It renders 3D avatar assets using Three.js / React Three Fiber. The backend provides an authenticated, private binary GLB streaming contract (`/api/v1/avatar/assets/{avatar_id}.glb`).

---

## 2. System Context Diagram

```mermaid
flowchart TD
    subgraph Users["Platform Users"]
        Consumer["Shopper / Consumer<br>(Inputs measurements, adjusts sliders, views fit)"]
        Merchant["Brand / Merchant<br>(Uploads garment specifications & size charts)"]
    end

    subgraph ClientTier["Client Presentation Tier"]
        WebClient["WearWise Web Client<br>(React 19 + Vite + React Three Fiber)<br>Port: 5173"]
    end

    subgraph BackendTier["Modular Monolith Backend (FastAPI)"]
        APIGateway["FastAPI Core & Router Engine<br>(/api/v1 REST endpoints, Auth Middleware)<br>Port: 8000"]
        
        subgraph AppServices["Application Orchestration Services"]
            AvatarOrch["AvatarOrchestrationService<br>(Coordinates Profile -> BICE -> Engine -> Anthro -> Storage)"]
            FitOrch["FitOrchestrationService<br>(Coordinates Profile -> Garment -> FitEngine)"]
        end

        subgraph CoreDomainModules["Internal Domain & Engine Modules"]
            BICE["BICE Module (app.bice)<br>(Semantic Normalization & Bounds Enforcer)"]
            AvatarMod["Avatar Engine (app.avatar_engine)<br>(Interface & Anny Adapter)"]
            AnthroMod["Anthropometry Engine (app.anthropometry)<br>(Exact Mesh-Plane Slicing & Landmark Analysis)"]
            FitMod["Honest Fit Engine (app.fit_engine)<br>(Ease Calculation & Fit Scoring)"]
        end
    end

    subgraph StorageTier["Persistence & Asset Storage"]
        RelationalDB[("Relational Database<br>(SQLite WAL / PostgreSQL)")]
        AssetStore[("External Asset Storage<br>(Content-Addressable Filesystem / S3)")]
    end

    Consumer -->|HTTPS / REST| WebClient
    Merchant -->|HTTPS / REST| WebClient
    WebClient -->|REST JSON + Binary GLB Stream| APIGateway

    APIGateway --> AvatarOrch
    APIGateway --> FitOrch

    AvatarOrch --> BICE
    AvatarOrch --> AvatarMod
    AvatarOrch --> AnthroMod
    AvatarOrch --> RelationalDB
    AvatarOrch --> AssetStore

    FitOrch --> FitMod
    FitOrch --> RelationalDB
```

---

## 3. Backend Component Architecture & Dependency Rules

### 3.1 Strict Authoritative Dependency Hierarchy
Dependencies flow strictly downward. Lower layers have zero knowledge of higher layers:

```mermaid
flowchart TD
    subgraph Layer1["1. API Layer (app.api)"]
        Routers["FastAPI Routers<br>(/profiles, /measurements, /controls, /avatar, /garments, /fit)"]
    end

    subgraph Layer2["2. Application Service Layer (app.services)"]
        AvatarOrch["AvatarOrchestrationService"]
        FitOrch["FitOrchestrationService"]
        StorageSvc["AssetStorageService"]
    end

    subgraph Layer3["3. Domain Engine Layer (app.domain, app.bice, app.avatar_engine, app.anthropometry, app.fit_engine)"]
        BICE["BICE<br>(Input: Controls, ShapeEvaluationPort -> Output: AvatarShapeSpec)"]
        AvatarEngine["AvatarEngine (Interface)<br>(Input: AvatarShapeSpec -> Output: MeshData, GLB bytes)"]
        Anthro["AnthropometryEngine<br>(Input: MeshData, LandmarkProvider -> Output: Measurements)"]
        FitEngine["HonestFitEngine<br>(Input: Body & Garment Measurements -> Output: FitResult)"]
        DomainContracts["Domain Entities & Interfaces<br>(BodyProfile, BodyMeasurement, GarmentProfile, ShapeEvaluationPort)"]
    end

    subgraph Layer4["4. Infrastructure & Persistence Layer (app.infrastructure)"]
        Repositories["ProfileRepository, GarmentRepository"]
        DiskStorage["FilesystemAssetStorageProvider"]
        Adapters["AnnyAdapter (Isolated)"]
    end

    Layer1 --> Layer2
    Layer2 --> Layer3
    Layer2 --> Layer4
    Layer3 --> DomainContracts
    Layer4 --> DomainContracts
    Adapters -.->|Implements| AvatarEngine
    Adapters -.->|Implements| DomainContracts
```

### 3.2 Clear Package Structure (Separation of Domain, Transport, and Persistence)
To prevent transport concerns or ORM decorators from polluting domain logic, the codebase enforces distinct package roots:
- **`app/domain/entities/`:** Pure Python dataclasses / domain entities (`BodyProfile`, `BodyMeasurement`, `AvatarShapeSpec`). Zero framework dependencies.
- **`app/domain/interfaces/`:** Abstract domain protocols (`AvatarEngine`, `ShapeEvaluationPort`, `LandmarkProvider`, `StorageProvider`).
- **`app/schemas/`:** Pydantic v2 schemas used strictly for HTTP request/response validation and serialization.
- **`app/infrastructure/models/`:** SQLAlchemy 2.0 ORM models mapped to relational tables.

---

## 4. End-to-End Orchestrated Data Flows

### 4.1 Avatar Generation Sequence Diagram (Orchestration Service Driven)

```mermaid
sequenceDiagram
    autonumber
    actor User as Authenticated Client
    participant API as FastAPI Router (/api/v1/avatar)
    participant Orch as AvatarOrchestrationService
    participant Repo as ProfileRepository
    participant BICE as BICE Module
    participant Engine as AvatarEngine (Interface)
    participant Adapter as AnnyAdapter (Isolated)
    participant Anthro as AnthropometryEngine
    participant Storage as AssetStorageService

    User->>API: POST /api/v1/avatar/generate {profile_id}
    Note over API: 1. Verify user ownership from auth principal<br/>2. Check Idempotency-Key
    API->>Orch: GenerateAvatarForProfile(user_id, profile_id)

    Orch->>Repo: GetActiveProfileRevision(profile_id)
    Repo-->>Orch: BodyProfile(rev_N, measurements, controls)

    Orch->>Engine: GetShapeEvaluationPort()
    Engine-->>Orch: ShapeEvaluationPort (Implemented by AnnyAdapter)

    Orch->>BICE: ComputeShapeSpec(measurements, controls, ShapeEvaluationPort)
    Note over BICE: 1. Normalize sliders [0, 1]<br/>2. Optional iterative locality check via ShapeEvaluationPort<br/>3. Synthesize neutral AvatarShapeSpec
    BICE-->>Orch: AvatarShapeSpec

    Orch->>Engine: GenerateAvatar(AvatarShapeSpec)
    Engine->>Adapter: ForwardPass(AvatarShapeSpec)
    Note over Adapter: 1. Map spec to Anny phenotypes & θ<br/>2. Clamp parameter bounds (log warnings)<br/>3. PyTorch CPU LBS forward pass (20.82 ms)
    Adapter-->>Engine: MeshData(vertices in METERS, faces)
    Engine-->>Orch: MeshData

    Orch->>Engine: GetLandmarkProvider()
    Engine-->>Orch: LandmarkProvider

    Orch->>Anthro: ExtractMeasurements(MeshData, LandmarkProvider)
    Note over Anthro: 1. Exact triangle-mesh-plane intersections<br/>2. Stitch closed contour loops<br/>3. Select anatomical loops via landmark proximity<br/>4. Calculate perimeters (cm)
    Anthro-->>Orch: ExtractedMeasurements (chest, waist, hips, etc.)

    Orch->>Engine: ExportGLB(MeshData)
    Engine->>Adapter: SerializeBinaryGLB(MeshData)
    Adapter-->>Engine: raw_glb_bytes
    Engine-->>Orch: raw_glb_bytes

    Orch->>Storage: StoreAvatarAsset(raw_glb_bytes)
    Note over Storage: 1. Compute SHA-256 digest<br/>2. Save to /data/assets/glb/{sha256}.glb<br/>3. Return asset metadata
    Storage-->>Orch: AssetRecord(asset_id, sha256, size_bytes, storage_uri)

    Orch->>Repo: PersistAvatarGeneration(profile_id, new_rev, AssetRecord, ExtractedMeasurements)
    Repo-->>Orch: Acknowledge Saved Revision

    Orch-->>API: AvatarGenerationResult(avatar_id, asset_url, ExtractedMeasurements)
    API-->>User: 200 OK (AvatarGenerationResponse)
```

### 4.2 Authenticated GLB Delivery Flow (Private No-Store Policy)

```mermaid
sequenceDiagram
    autonumber
    actor Browser as React Three Fiber (Web Client)
    participant API as FastAPI Router (/api/v1/avatar/assets/{id}.glb)
    participant Storage as AssetStorageService

    Browser->>API: GET /api/v1/avatar/assets/{id}.glb<br/>Headers: Authorization / Cookie, If-None-Match: "sha256"
    Note over API: 1. Authenticate caller<br/>2. Verify user owns the avatar profile<br/>3. Check If-None-Match ETag
    
    alt ETag Matches & Asset Valid
        API-->>Browser: 304 Not Modified
    else ETag Differs / Fresh Request
        API->>Storage: ReadAssetBytes(asset_id)
        Storage-->>API: raw_glb_bytes
        API-->>Browser: 200 OK<br/>Content-Type: model/gltf-binary<br/>Cache-Control: private, no-store<br/>ETag: "sha256_hash"
    end
```

---

## 5. Architectural Decision Records (Revision 1.2)

### ADR-01: Modular Monolith Architecture
- **Status:** Approved.
- **Context:** Initial infrastructure budget is ₹0. Single-process execution eliminates network serialization and distributed deployment overhead.
- **Decision:** Build a single deployable Python FastAPI application structured into decoupled layers. In-process calls use typed domain models.

### ADR-02: CPU-Primary Inference Strategy
- **Status:** Approved.
- **Context:** Phase 0 proved single-mesh inference on an AMD Ryzen 7 6800H CPU takes **$20.82\text{ ms}$**, whereas single-mesh GPU inference on the RTX 3050 takes $74.45\text{ ms}$ due to CUDA kernel launch overhead.
- **Decision:** Default interactive avatar generation worker threads to run on CPU PyTorch tensors. CUDA execution is reserved for batch offline jobs.

### ADR-03: Two-Phase Authenticated GLB Asset Delivery Contract (`private, no-store`)
- **Status:** Approved (Revision 1.2).
- **Context:** Avatar assets represent personal 3D body representations. Shared public CDN caching violates user privacy.
- **Decision:** Serving requires authentication and returns `Cache-Control: private, no-store` with content-derived ETag (SHA-256).

### ADR-04: Strict Isolation of Avatar Engine & Application-Level Orchestration
- **Status:** Approved (Revision 1.2).
- **Context:** Coupling BICE or Anthropometry to Anny creates severe vendor lock-in. Avatar Engine must not orchestrate measurement extraction.
- **Decision:** `AvatarOrchestrationService` coordinates the workflow. BICE outputs `AvatarShapeSpec` and accesses displacement feedback through `ShapeEvaluationPort`. AnnyAdapter translates `AvatarShapeSpec` to Anny parameters and provides `LandmarkProvider`. Anthropometry operates strictly on neutral meshes and landmark coordinates.

### ADR-05: Atomic Content-Addressable Blob Deletion Synchronization
- **Status:** Approved (Revision 1.2.1).
- **Context:** Content-addressable storage (`/data/assets/glb/{sha256}.glb`) allows multiple avatars to share identical blobs. A Time-of-Check to Time-of-Use race condition could allow an outbox cleanup worker to delete a blob while another process registers a live reference to the same digest.
- **Decision:** Enforce mutual exclusion during asset registration and blob deletion:
  - Production (PostgreSQL): Scoped transactional advisory locks (`SELECT pg_advisory_xact_lock(hashtext(:sha256_checksum));`).
  - Development (SQLite): Serialized write transactions via `BEGIN IMMEDIATE`.
