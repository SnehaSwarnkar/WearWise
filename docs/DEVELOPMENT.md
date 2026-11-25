# WearWise Development & Operations Guide

## 1. Prerequisites

- **OS:** Windows 10/11 (PowerShell) or Linux/macOS
- **Node.js:** `20+` and `npm`
- **Python:** `3.12` (repository virtual environment located at `WEARWISE-BODY-ENGINE/.venv-anny`)
- **Playwright Chromium:** Required only for end-to-end browser verification (`playwright install chromium`)

---

## 2. Clean Checkout Installation

```powershell
# 1. Configure environment variables (copy template; never commit .env)
Copy-Item .env.example .env

# 2. Install Frontend dependencies
Set-Location frontend
npm install

# 3. Install Python dependencies inside virtualenv (if recreating venv)
Set-Location ..\WEARWISE-BODY-ENGINE
.\.venv-anny\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-anny\Scripts\python.exe -m pip install -r ..\backend\requirements.txt
```

---

## 3. Environment & VTON Provider Configuration

Edit `.env` cleanly (all staging runs override database names to `*_staging`):

- `MONGODB_URI`: MongoDB Atlas connection string (Commerce backend falls back to JSON storage if unset, while Body Engine MongoDB features require MongoDB).
- `MONGODB_BODY_ENGINE_DB=wearwise_body_engine_staging`
- `MONGODB_COMMERCE_DB=wearwise_commerce_staging`
- **Image Virtual Try-On (Optional — leave empty to keep Photo Try-On honestly unavailable):**
  - For **FASHN AI API v1**: set `VTON_PROVIDER=fashn` and `FASHN_API_KEY=<your-key>`
  - For **Custom HTTP / Vertex Proxy**: set `VTON_API_URL=<endpoint>` and `VTON_API_KEY=<token>`

---

## 4. Starting Staging Services

Open three PowerShell terminals from repository root:

```powershell
# Terminal 1 — Body & Garment Engine (port 8000)
$env:MONGODB_BODY_ENGINE_DB="wearwise_body_engine_staging"
$env:MONGODB_COMMERCE_DB="wearwise_commerce_staging"
Set-Location WEARWISE-BODY-ENGINE
.\.venv-anny\Scripts\python.exe -m uvicorn app.api.app:app --host 127.0.0.1 --port 8000

# Terminal 2 — Commerce API (port 8001)
$env:MONGODB_COMMERCE_DB="wearwise_commerce_staging"
$env:MONGODB_BODY_ENGINE_DB="wearwise_body_engine_staging"
Set-Location backend
..\WEARWISE-BODY-ENGINE\.venv-anny\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001

# Terminal 3 — Frontend Dev Server (port 3000) or Preview (port 4173)
Set-Location frontend
npm run dev -- --port 3000
```

Vite proxies `/api/products` to `127.0.0.1:8001` and `/api/*` to `127.0.0.1:8000` (see `frontend/vite.config.js`).

---

## 5. Verification Commands

```powershell
# Frontend unit tests + production bundle
Set-Location frontend
npm test -- --run
npm run build

# Commerce backend tests (run with backend/ as Cwd)
Set-Location ..\backend
$env:MONGODB_COMMERCE_DB="wearwise_commerce_staging"
$env:MONGODB_BODY_ENGINE_DB="wearwise_body_engine_staging"
..\WEARWISE-BODY-ENGINE\.venv-anny\Scripts\python.exe -m pytest tests -v

# Body Engine security, capability, VTON, and lifecycle tests (run with WEARWISE-BODY-ENGINE/ as Cwd)
Set-Location ..\WEARWISE-BODY-ENGINE
.\.venv-anny\Scripts\python.exe -m pytest tests/api/test_phase12_vton_and_capabilities.py tests/api/test_auth_security.py tests/api/test_merchant_lifecycle_m4_m5b.py -v
```
