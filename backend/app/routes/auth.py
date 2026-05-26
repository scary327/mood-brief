import logging
import re
import time
from collections import defaultdict, deque
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserRegister, UserLogin, TokenResponse, UserOut
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── In-process rate limit for login/register ────────────────────────────────
# Per-IP sliding window. This is intentionally small — for a single-node test
# deployment behind nginx it's enough to slow down credential brute force.
# For multi-node prod replace with Redis-backed slowapi.
_RATE_WINDOW_SECONDS = 60
_RATE_MAX_REQUESTS = 10
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    # nginx sets X-Forwarded-For; trust only the leftmost value.
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(request: Request, bucket: str) -> None:
    key = f"{bucket}:{_client_ip(request)}"
    now = time.monotonic()
    q = _rate_buckets[key]
    cutoff = now - _RATE_WINDOW_SECONDS
    while q and q[0] < cutoff:
        q.popleft()
    if len(q) >= _RATE_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Try again in a minute.",
        )
    q.append(now)


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password requirements.
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[a-zA-Z]", password):
        return False, "Password must contain at least one letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit"
    return True, ""


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: UserRegister, request: Request, db: Session = Depends(get_db)):
    """Register a new user."""
    _check_rate_limit(request, "register")
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == body.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Validate password
    is_valid, error_msg = validate_password(body.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    # Create user
    user = User(
        email=body.email,
        username=body.username,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    logger.info(f"User registered: {user.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }


@router.post("/login", response_model=TokenResponse)
def login(
    body: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Authenticate user and return tokens."""
    _check_rate_limit(request, "login")
    # Find user by email
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        logger.warning(f"Login failed: User not found for email {body.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(body.password, user.password_hash):
        logger.warning(f"Login failed: Invalid password for email {body.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Set refresh token as httpOnly cookie. secure/samesite are
    # configurable so the same code works for HTTP test servers and HTTPS
    # production — see settings.COOKIE_SECURE / COOKIE_SAMESITE.
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )

    logger.info(f"User logged in: {user.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,  # Also return in body for mobile/SPA
    }


@router.post("/refresh-token", response_model=TokenResponse)
def refresh_token_endpoint(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Refresh endpoint that accepts refresh token from httpOnly cookie.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    user = verify_refresh_token(refresh_token, db)

    # Generate new access token
    new_access_token = create_access_token(data={"sub": str(user.id)})

    # Optionally generate new refresh token for rotation
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token,
    }
