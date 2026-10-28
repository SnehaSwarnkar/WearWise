# WearWise — AI Fashion App

WearWise is a full-stack AI fashion application that helps users discover their personal style, virtually try on clothes, manage a digital wardrobe, and shop with confidence.

---

## ✦ Features

| Feature | Description |
|---|---|
| **Explore** | Browse a curated product catalogue with category filters and price sorting. Add items to bag or wishlist in one click. |
| **My Style** | Upload a photo or build an avatar to kick off your personalised style journey. |
| **Build Avatar** | Create a style profile manually (colour direction, body type, fit, vibe) or let AI analyse a photo and suggest a starter profile. |
| **Virtual Try-On** | Upload your photo → choose a look → see the result. Three-step guided flow. |
| **Style Analysis** | AI-generated style results showing your colour profile, style vibe and body profile. |
| **Wardrobe** | Upload and manage your own clothing pieces in a digital closet, organised by category. |
| **Saved Looks & Wishlist** | Save outfits you love and keep products on your wishlist for later. |
| **Shopping Cart** | Add products, adjust quantities, and proceed to checkout with live order totals and free-shipping logic. |
| **Checkout** | Full checkout form (contact, delivery address, payment method) with order confirmation. |
| **Fashion Assistant** | An AI chat stylist that gives contextual outfit advice based on your style profile. |

---

## 🗂 Project Structure

```
ai-fashion/
├── frontend/                  # React + Vite
│   ├── src/
│   │   ├── api/               # API client layer (one file per domain)
│   │   │   ├── client.js      # Base fetch wrapper + session ID
│   │   │   ├── products.js
│   │   │   ├── cart.js
│   │   │   ├── orders.js
│   │   │   ├── avatar.js
│   │   │   ├── wardrobe.js
│   │   │   ├── saved.js
│   │   │   ├── assistant.js
│   │   │   └── tryon.js
│   │   ├── pages/             # One component per route
│   │   │   ├── Home.jsx
│   │   │   ├── Explore.jsx
│   │   │   ├── MyStyle.jsx
│   │   │   ├── BuildAvatar.jsx
│   │   │   ├── TryOn.jsx
│   │   │   ├── ChooseLook.jsx
│   │   │   ├── StyleAnalysis.jsx
│   │   │   ├── Wardrobe.jsx
│   │   │   ├── SavedLooks.jsx
│   │   │   ├── FashionAssistant.jsx
│   │   │   ├── Cart.jsx
│   │   │   ├── Checkout.jsx
│   │   │   ├── OrderConfirmation.jsx
│   │   │   └── Header.jsx
│   │   ├── App.jsx            # Route definitions
│   │   ├── App.css            # Global stylesheet
│   │   └── main.jsx           # Entry point
│   ├── .env                   # VITE_API_URL
│   └── package.json
│
└── backend/                   # Python + FastAPI
    ├── app/
    │   ├── main.py            # App entry point, CORS, static mounts
    │   ├── database.py        # JSON-file data layer
    │   ├── routers/
    │   │   ├── products.py
    │   │   ├── cart.py
    │   │   ├── orders.py
    │   │   ├── avatar.py
    │   │   ├── wardrobe.py
    │   │   ├── saved.py
    │   │   ├── assistant.py
    │   │   └── tryon.py
    │   └── schemas/           # Pydantic request/response models
    │       ├── products.py
    │       ├── cart.py
    │       ├── orders.py
    │       ├── avatar.py
    │       ├── wardrobe.py
    │       ├── saved.py
    │       └── assistant.py
    ├── uploads/               # Uploaded images (gitignored)
    ├── data/                  # JSON data files (gitignored)
    ├── requirements.txt
    └── run.sh
```

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** v18+
- **Python** 3.11+

---

### 1. Clone the repo

```bash
git clone https://github.com/your-username/ai-fashion.git
cd ai-fashion
```

---

### 2. Backend setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv fastapi_env
source fastapi_env/bin/activate      # macOS / Linux
# fastapi_env\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt
```

**Start the backend:**

```bash
./run.sh
# or manually:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be running at `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

---

### 3. Frontend setup

```bash
cd frontend
npm install
```

Create a `.env` file (already included, but verify it contains):

```
VITE_API_URL=http://localhost:8000
```

**Start the dev server:**

```bash
npm run dev
```

The app will be running at `http://localhost:5173`

---

## 🔌 API Overview

The backend exposes 34 REST endpoints across 8 routers. Full interactive docs are available at `http://localhost:8000/docs` when the server is running.

| Router | Base Path | Responsibility |
|---|---|---|
| Products | `/api/products` | Catalogue listing, filters, single product |
| Cart | `/api/cart` | Add, update quantity, remove, clear |
| Orders | `/api/orders` | Place order, order history, order detail |
| Avatar | `/api/avatar` | Save style profile, fetch profile, AI photo analysis |
| Wardrobe | `/api/wardrobe` | Upload clothes, list, rename, delete |
| Saved | `/api/saved` | Saved looks + wishlist CRUD |
| Assistant | `/api/assistant` | AI fashion chat |
| Try-On | `/api/tryon` | Photo upload, look processing, result fetch |

Sessions are anonymous and identified by a `session_id` generated in the browser (`sessionStorage`). No login required.

---

## 🛠 Tech Stack

**Frontend**
- [React 19](https://react.dev/) with [React Router v7](https://reactrouter.com/)
- [Vite 8](https://vitejs.dev/) — build tool and dev server
- Vanilla CSS — custom design system with CSS variables

**Backend**
- [FastAPI 0.115](https://fastapi.tiangolo.com/) — async Python API framework
- [Uvicorn](https://www.uvicorn.org/) — ASGI server
- [Pydantic v2](https://docs.pydantic.dev/) — request/response validation
- JSON file storage — zero-config, swap for any database
- `python-multipart` — file upload handling
- `aiofiles` — async file I/O

---

## 📸 App Pages

| Route | Page |
|---|---|
| `/` | Home — hero, style journey, category preview |
| `/explore` | Product catalogue with filters |
| `/my-style` | Style entry point — upload or build avatar |
| `/build-avatar` | Avatar builder (manual or AI-assisted) |
| `/try-on` | Step 1 — upload your photo |
| `/choose-look` | Step 2 — pick your style |
| `/style-analysis` | Step 3 — view AI style results |
| `/wardrobe` | Digital wardrobe manager |
| `/saved` | Saved looks and wishlist |
| `/fashion-assistant` | AI chat stylist |
| `/cart` | Shopping bag |
| `/checkout` | Order form and payment |
| `/order-confirmation` | Order placed confirmation |

---

## 🧩 Extending the App

**Swap to a real database**
All data access goes through `backend/app/database.py`. Replace the JSON-file functions with SQLAlchemy, MongoDB Motor, or any other ORM — the routers don't change.

**Add real AI try-on**
The `/api/tryon/process` endpoint has a clearly marked placeholder comment. Replace it with your CV model or a third-party try-on API call.

**Add real AI chat**
`backend/app/routers/assistant.py` has an isolated `_generate_reply()` function. Swap its body for an OpenAI / Anthropic API call to upgrade the assistant.

**Add authentication**
The `session_id` in `frontend/src/api/client.js` can be replaced with a JWT token. The backend schemas already accept `session_id` as a string — update it to come from an auth header instead.

---

## 📄 License

MIT
