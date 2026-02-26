from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

app = FastAPI(title="MoodBrief API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ────────────────────────────────────────────────────────────────────


class MoodIn(BaseModel):
    mood: str  # e.g. "happy", "sad", "neutral"
    note: Optional[str] = None


class MoodOut(MoodIn):
    id: int
    created_at: datetime


# ── Fake in-memory store ──────────────────────────────────────────────────────

_moods: list[MoodOut] = [
    MoodOut(id=1, mood="happy", note="Great morning!", created_at=datetime(2026, 2, 26, 8, 0)),
    MoodOut(id=2, mood="neutral", note=None, created_at=datetime(2026, 2, 26, 9, 0)),
    MoodOut(id=3, mood="sad", note="Tired after work", created_at=datetime(2026, 2, 26, 10, 0)),
]
_next_id = 4


# ── Routes ────────────────────────────────────────────────────────────────────


@app.get("/health")
def health():
    return {"status": "ok", "service": "mood-brief-backend"}


@app.get("/api/moods", response_model=list[MoodOut])
def list_moods():
    """Return all recorded moods."""
    return _moods


@app.post("/api/moods", response_model=MoodOut, status_code=201)
def create_mood(payload: MoodIn):
    """Record a new mood entry."""
    global _next_id
    entry = MoodOut(
        id=_next_id,
        mood=payload.mood,
        note=payload.note,
        created_at=datetime.utcnow(),
    )
    _moods.append(entry)
    _next_id += 1
    return entry


@app.get("/api/moods/{mood_id}", response_model=MoodOut)
def get_mood(mood_id: int):
    """Return a single mood by id."""
    for m in _moods:
        if m.id == mood_id:
            return m
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Mood not found")
