# WearWise — AI Personal Fashion Stylist

A full-stack AI fashion platform with hand-drawn illustration design, virtual try-on, avatar builder, AI stylist chat, and a complete shop.

---

## 🏗️ Project Structure

```
fashion/
│
├── frontend/                   ← React + Vite frontend
│   ├── src/
│   │   ├── api/                ← API service layer (10 files)
│   │   ├── context/            ← AuthContext, ThemeContext
│   │   ├── pages/              ← All page components + CSS
│   │   ├── components/         ← Shared components
│   │   ├── styles/             ← Global design system CSS
│   │   ├── data/               ← Static data (collections)
│   │   ├── App.jsx             ← Route definitions
│   │   ├── main.jsx            ← Entry point
│   │   ├── index.css
│   │   ├── App.css
│   │   └── wearwise.css        ← Global CSS variables + tokens
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example            ← Frontend env template
│
├── backend/                    ← FastAPI Python backend
│   ├── app/
│   │   ├── main.py             ← FastAPI app, CORS, router registration
│   │   ├── database.py         ← JSON file DB (no external DB needed)
│   │   ├── routers/            ← 10 API route handlers
│   │   │   ├── auth.py         ← /api/auth/*
│   │   │   ├── products.py     ← /api/products/*
│   │   │   ├── catalogue.py    ← /api/catalogue/{gender}
│   │   │   ├── cart.py         ← /api/cart/*
│   │   │   ├── orders.py       ← /api/orders/*
│   │   │   ├── avatar.py       ← /api/avatar/*
│   │   │   ├── wardrobe.py     ← /api/wardrobe/*
│   │   │   ├── saved.py        ← /api/saved/*
│   │   │   ├── assistant.py    ← /api/assistant/chat
│   │   │   └── tryon.py        ← /api/tryon/*
│   │   └── schemas/            ← Pydantic request/response models
│   ├── data/                   ← JSON collection files (auto-created, not in Git)
│   ├── uploads/                ← User-uploaded files (auto-created, not in Git)
│   │   ├── tryon/
│   │   ├── wardrobe/
│   │   └── avatars/
│   ├── venv/                   ← Python virtual environment (not in Git)
│   ├── requirements.txt
│   ├── run.sh                  ← Convenience start script
│   └── .env.example            ← Backend env template
│
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### 1. Backend

```bash
cd fashion/backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate       # macOS / Linux
# venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt

# Start the server (auto-reload on changes)
./run.sh
# OR: uvicorn app.main:app --reload --port 8000
```

Backend runs at: **http://localhost:8000**
Swagger docs: **http://localhost:8000/docs**

### 2. Frontend

```bash
cd fashion/frontend

# Copy and configure environment
cp .env.example .env
# Edit .env if your backend runs on a different port

# Install dependencies (first time only)
npm install

# Start Vite dev server
npm run dev
```

Frontend runs at: **http://localhost:5173**

---

## 🔌 API Route Map

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/auth/signup` | Register new user |
| POST | `/api/auth/login` | Login, returns token |
| GET | `/api/auth/me` | Get current user (Bearer token) |
| PATCH | `/api/auth/profile` | Update gender / body profile |
| GET | `/api/products/` | List all products |
| GET | `/api/products/{id}` | Single product |
| GET | `/api/catalogue/{gender}` | Shop by gender + filters |
| GET | `/api/cart/{session_id}` | Get cart |
| POST | `/api/cart/add` | Add item to cart |
| PUT | `/api/cart/update` | Update item quantity |
| DELETE | `/api/cart/{session_id}/{item_id}` | Remove item |
| DELETE | `/api/cart/{session_id}` | Clear cart |
| POST | `/api/orders/place` | Place order |
| GET | `/api/orders/my` | My orders (auth required) |
| GET | `/api/orders/detail/{id}` | Order detail |
| POST | `/api/avatar/save` | Save avatar / style profile |
| GET | `/api/avatar/{session_id}` | Get avatar profile |
| POST | `/api/avatar/analyze-photo` | AI photo analysis |
| POST | `/api/wardrobe/upload` | Upload clothing images |
| GET | `/api/wardrobe/{session_id}` | List wardrobe items |
| PATCH | `/api/wardrobe/{item_id}` | Update wardrobe item |
| DELETE | `/api/wardrobe/{item_id}` | Delete wardrobe item |
| POST | `/api/saved/looks` | Save a look |
| GET | `/api/saved/looks/{session_id}` | List saved looks |
| DELETE | `/api/saved/looks/{look_id}` | Remove saved look |
| POST | `/api/saved/wishlist` | Add to wishlist |
| GET | `/api/saved/wishlist/{session_id}` | List wishlist |
| DELETE | `/api/saved/wishlist/{item_id}` | Remove from wishlist |
| POST | `/api/assistant/chat` | AI stylist chat |
| POST | `/api/tryon/upload-photo` | Upload user photo |
| POST | `/api/tryon/process` | Apply look to photo |
| GET | `/api/tryon/{session_id}` | Get try-on result |

---

## 🗄️ Where Data is Stored

| Layer | Location | Contents |
|-------|----------|----------|
| Backend DB | `backend/data/*.json` | Users, carts, orders, avatars, wardrobe, saved looks, wishlist, tryon sessions |
| Uploads | `backend/uploads/` | User photos (wardrobe, try-on, avatar) |
| Browser localStorage | `ww-auth-token`, `ww-user`, `wearwise-last-order` | Auth token, user cache, last order |
| Browser sessionStorage | `ww-session-id` | Anonymous session ID for cart/wardrobe |

---

## 🔐 Environment Variables

### Frontend (`frontend/.env`)
```
VITE_API_URL=http://localhost:8000
```

### Backend (`backend/.env.example`)
```
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
SECRET_KEY=change-me-to-a-long-random-secret-in-production
```

---

## ⚠️ Known Limitations

| Feature | Status | Notes |
|---------|--------|-------|
| Virtual Try-On AI | Simulated | Returns original photo. Integrate a real model in `backend/app/routers/tryon.py` |
| Avatar Photo Analysis | Simulated | Rule-based profile. Integrate a CV model in `backend/app/routers/avatar.py` |
| AI Stylist | Rule-based | Keyword detection. Replace `_generate_reply()` with an LLM call |
| Auth tokens | Simple SHA-256 | Upgrade to JWT (`python-jose` already installed) |
| Database | JSON files | Upgrade to PostgreSQL / MongoDB for production |
