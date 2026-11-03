# WearWise — AI Fashion App

WearWise is a full-stack AI fashion application that helps users discover their personal style, virtually try on clothes, manage a digital wardrobe, and shop with confidence. It features a complete onboarding flow, gender-specific shops, and a unified design system across all pages.

---

## ✦ Features

| Feature | Description |
|---|---|
| **Login / Signup** | Email + password authentication with token-based sessions |
| **Gender Onboarding** | Select Men, Women or Kids — each with a dedicated body-type setup step |
| **Body Type Setup** | 6 body type options for Men and Women; Boys/Girls + age group for Kids |
| **Gender-Specific Shops** | Separate shops for Men, Women and Kids with occasion + category filters |
| **Header Dropdown** | Hover "Shop" in the nav to get a Gender dropdown with an Occasion fly-out sub-menu |
| **Explore** | Browse a curated product catalogue with category tabs and price sorting |
| **My Style** | Upload a photo or build an avatar to kick off your personalised style journey |
| **Build Avatar** | Create a style profile manually or let AI analyse a photo |
| **Virtual Try-On** | Upload your photo → choose a look → see the result (3-step guided flow) |
| **Style Analysis** | AI-generated style results showing colour profile, vibe and body profile |
| **Wardrobe** | Upload and manage your own clothing pieces in a digital closet |
| **Saved Looks & Wishlist** | Save outfits you love and keep products on your wishlist |
| **Shopping Cart** | Add products, adjust quantities, proceed to checkout |
| **Checkout** | Full checkout form (contact, delivery, payment) with order confirmation |
| **Fashion Assistant** | AI chat stylist giving contextual advice based on your style profile |

---

## 🗂 Project Structure

```
ai-fashion/
├── frontend/                      # React + Vite
│   ├── src/
│   │   ├── api/                   # API client layer (one file per domain)
│   │   │   ├── client.js          # Base fetch wrapper + session ID
│   │   │   ├── auth.js            # Login, signup, profile update
│   │   │   ├── catalogue.js       # Gender-specific shop catalogue
│   │   │   ├── products.js        # General explore products
│   │   │   ├── cart.js
│   │   │   ├── orders.js
│   │   │   ├── avatar.js
│   │   │   ├── wardrobe.js
│   │   │   ├── saved.js
│   │   │   ├── assistant.js
│   │   │   └── tryon.js
│   │   ├── context/
│   │   │   └── AuthContext.jsx    # Global auth state + PrivateRoute
│   │   ├── pages/
│   │   │   ├── Login.jsx          # Sign-in page
│   │   │   ├── Signup.jsx         # Registration page
│   │   │   ├── GenderSelect.jsx   # Step 1 — choose Men / Women / Kids
│   │   │   ├── MenSetup.jsx       # Step 2 — men's body type
│   │   │   ├── WomenSetup.jsx     # Step 2 — women's body type
│   │   │   ├── KidsSetup.jsx      # Step 2 — kids gender + age group
│   │   │   ├── MenShop.jsx        # Men's shop page
│   │   │   ├── WomenShop.jsx      # Women's shop page
│   │   │   ├── KidsShop.jsx       # Kids' shop with Boys/Girls toggle
│   │   │   ├── ShopLayout.jsx     # Shared shop layout component
│   │   │   ├── Header.jsx         # Sticky nav with gender dropdown
│   │   │   ├── Home.jsx
│   │   │   ├── Explore.jsx        # Unified product grid
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
│   │   │   └── OrderConfirmation.jsx
│   │   ├── App.jsx                # All routes + PrivateRoute guard
│   │   ├── App.css                # Unified design system
│   │   └── main.jsx               # Entry point (wraps in AuthProvider)
│   ├── .env                       # VITE_API_URL
│   └── package.json
│
└── backend/                       # Python + FastAPI
    ├── app/
    │   ├── main.py                # App entry, CORS, static mounts
    │   ├── database.py            # JSON-file data layer
    │   ├── routers/
    │   │   ├── auth.py            # Signup, login, me, profile update
    │   │   ├── catalogue.py       # Gender-specific product catalogue
    │   │   ├── products.py        # General explore products
    │   │   ├── cart.py
    │   │   ├── orders.py
    │   │   ├── avatar.py
    │   │   ├── wardrobe.py
    │   │   ├── saved.py
    │   │   ├── assistant.py
    │   │   └── tryon.py
    │   └── schemas/               # Pydantic models
    │       ├── auth.py
    │       ├── products.py
    │       ├── cart.py
    │       ├── orders.py
    │       ├── avatar.py
    │       ├── wardrobe.py
    │       ├── saved.py
    │       └── assistant.py
    ├── uploads/                   # Uploaded images (gitignored)
    ├── data/                      # JSON data files (gitignored)
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
git clone https://github.com/SnehaSwarnkar/WearWise.git
cd WearWise
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

API running at `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

---

### 3. Frontend setup

```bash
cd frontend
npm install
```

Verify `.env` contains:

```
VITE_API_URL=http://localhost:8000
```

**Start the dev server:**

```bash
npm run dev
```

App running at `http://localhost:5173`

---

## 🔄 User Flow

```
/login  ──→  /signup
  │
  ▼
/select-gender  ──→  Men / Women / Kids
  │
  ├── Men    ──→  /men-setup   (body type)   ──→  /men-shop
  ├── Women  ──→  /women-setup (body type)   ──→  /women-shop
  └── Kids   ──→  /kids-setup  (gender+age)  ──→  /kids-shop
```

Each shop has:
- **Category tabs** — All / Western / Traditional / Indo-Western / Occasion Wear
- **Occasion filter** — Casual / Work / Festive / Wedding / Party
- **Price sort** — toggle ascending by price
- **Add to Bag** — adds to server-side cart
- **Try On** — links to the virtual try-on flow

---

## 🔌 API Overview

The backend exposes **39 REST endpoints** across 10 routers.

| Router | Base Path | Responsibility |
|---|---|---|
| Auth | `/api/auth` | Signup, login, get current user, update profile |
| Catalogue | `/api/catalogue/{gender}` | Gender + category + occasion filtered products |
| Products | `/api/products` | General explore catalogue |
| Cart | `/api/cart` | Add, update, remove, clear |
| Orders | `/api/orders` | Place order, history, detail |
| Avatar | `/api/avatar` | Save profile, fetch profile, AI photo analysis |
| Wardrobe | `/api/wardrobe` | Upload clothes, list, rename, delete |
| Saved | `/api/saved` | Saved looks + wishlist CRUD |
| Assistant | `/api/assistant` | AI fashion chat |
| Try-On | `/api/tryon` | Photo upload, look processing, result fetch |

### Auth flow

All authenticated endpoints require:

```
Authorization: Bearer <token>
```

The token is returned on login/signup and stored in `localStorage`. The frontend reads it from `AuthContext` and attaches it to every protected API call.

---

## 🛠 Tech Stack

**Frontend**
- [React 19](https://react.dev/) + [React Router v7](https://reactrouter.com/)
- [Vite 8](https://vitejs.dev/)
- Vanilla CSS — unified design system with CSS variables

**Backend**
- [FastAPI 0.115](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/) — ASGI server
- [Pydantic v2](https://docs.pydantic.dev/) — request/response validation
- JSON file storage (zero-config, swap for any DB)
- `python-multipart` — file upload handling

---

## 📸 All Routes

| Route | Page |
|---|---|
| `/login` | Sign in |
| `/signup` | Create account |
| `/select-gender` | Choose Men / Women / Kids |
| `/men-setup` | Men's body type selection |
| `/women-setup` | Women's body type selection |
| `/kids-setup` | Kids gender + age group |
| `/men-shop` | Men's shop — Western, Traditional, Indo-Western, Occasion |
| `/women-shop` | Women's shop |
| `/kids-shop` | Kids' shop with Boys/Girls toggle |
| `/` | Home |
| `/explore` | Product catalogue |
| `/my-style` | Style entry point |
| `/build-avatar` | Avatar builder |
| `/try-on` | Step 1 — upload photo |
| `/choose-look` | Step 2 — pick style |
| `/style-analysis` | Step 3 — AI style results |
| `/wardrobe` | Digital wardrobe |
| `/saved` | Saved looks + wishlist |
| `/fashion-assistant` | AI chat stylist |
| `/cart` | Shopping bag |
| `/checkout` | Order form + payment |
| `/order-confirmation` | Order confirmed |

---

## 🎨 Design System

All pages share a single CSS variable set:

```css
--black:  #151515
--cream:  #fff8f1
--pink:   #ff3d9a
--orange: #ff633d
--lime:   #d8ff3f
--purple: #8d6bff
```

Unified component classes used across Explore, MenShop, WomenShop and KidsShop:

| Class | Purpose |
|---|---|
| `.unified-controls` | Controls bar (category + sort) |
| `.unified-tab` / `.unified-tab-active` | Category filter buttons |
| `.unified-select` | Styled select dropdown |
| `.unified-sort-btn` / `.unified-sort-active` | Sort button |
| `.unified-grid` | Product grid |
| `.shop-card` | Product card |
| `.shop-card-image` | Card image area |
| `.shop-card-info` | Name + price + colour dots |
| `.shop-card-actions` | Add to Bag + Try On buttons |

---

## 🧩 Extending the App

**Swap to a real database**  
All data access goes through `backend/app/database.py`. Replace the JSON functions with SQLAlchemy, MongoDB Motor, or any ORM — the routers stay unchanged.

**Add real AI try-on**  
`/api/tryon/process` has a clearly marked placeholder. Replace it with your CV model or a third-party API call.

**Add real AI chat**  
`_generate_reply()` in `backend/app/routers/assistant.py` is isolated. Swap its body for an OpenAI / Anthropic call.

**Add authentication middleware**  
The current token is a SHA-256 hash. Swap it for JWT using `python-jose` (already installed) for production-grade auth.

---

## 📄 License

MIT
