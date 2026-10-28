"""
WearWise FastAPI Backend
========================
Entry point. Registers all routers, configures CORS for the Vite dev server,
and mounts the uploads directory as a static file endpoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routers import products, cart, orders, avatar, wardrobe, saved, assistant, tryon

# ── App instance ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="WearWise API",
    description=(
        "Backend for the WearWise AI Fashion app. "
        "Serves products, cart, orders, avatar profiles, wardrobe, "
        "saved looks, wishlist, virtual try-on and the AI fashion assistant."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS ──────────────────────────────────────────────────────────────────────
# Allows the Vite dev server (port 5173) to call the API (port 8000).
# Tighten origins for production.

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Static uploads ────────────────────────────────────────────────────────────
# Uploaded images (wardrobe, try-on, avatar) are served from /uploads/

UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(avatar.router)
app.include_router(wardrobe.router)
app.include_router(saved.router)
app.include_router(assistant.router)
app.include_router(tryon.router)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": "WearWise API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
