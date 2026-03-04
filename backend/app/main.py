import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routes import analyze, brief, history

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="MoodBrief API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ─────────────────────────────────────────────────────────

app.include_router(analyze.router)
app.include_router(brief.router)
app.include_router(history.router)


# ── Startup ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    """Create tables if they don't exist yet."""
    Base.metadata.create_all(bind=engine)
    logging.info("Database tables ensured.")


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "mood-brief-backend", "version": "0.2.0"}
