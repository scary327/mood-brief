import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routes import analyze, brief, projects, feedback, auth


logging.basicConfig(level=logging.INFO)

app = FastAPI(title="MoodBrief API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    # Match any VS Code devtunnels host (e.g. https://abc-3000.euw.devtunnels.ms)
    # so we don't have to edit BACKEND_CORS_ORIGINS every time the tunnel ID
    # rotates or a new port is forwarded.
    allow_origin_regex=r"https://[a-z0-9-]+\.[a-z0-9-]+\.devtunnels\.ms",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse
from fastapi import Request


def _allowed_origin(request: Request) -> str | None:
    """Echo the request Origin back when it is in the configured allow-list
    or matches the devtunnels regex. Used by the global exception handler so
    500 responses still carry valid CORS headers."""
    origin = request.headers.get("origin")
    if not origin:
        return None
    if origin in settings.BACKEND_CORS_ORIGINS:
        return origin
    import re
    if re.fullmatch(r"https://[a-z0-9-]+\.[a-z0-9-]+\.devtunnels\.ms", origin):
        return origin
    return None


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import logging
    logging.error(f"Global exception: {str(exc)}", exc_info=True)
    headers: dict[str, str] = {}
    origin = _allowed_origin(request)
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Vary"] = "Origin"
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
        headers=headers,
    )

# ── Register routers ─────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(analyze.router)
app.include_router(brief.router)
app.include_router(projects.router)
app.include_router(feedback.router)



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
