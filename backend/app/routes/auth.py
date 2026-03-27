import logging
import re
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
def register(body: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
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
def login(body: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Authenticate user and return tokens."""
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

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # Set to True in production (HTTPS only)
        samesite="strict",
        max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )

    logger.info(f"User logged in: {user.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,  # Also return in body for mobile/SPA
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh(request_cookies: dict = None, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token from cookies.
    For manual refresh: pass refresh_token in Authorization header as Bearer token.
    """
    # Try to get refresh token from cookies (for web)
    from fastapi import Request

    def get_refresh_token(req: Request):
        return req.cookies.get("refresh_token")

    # This is a workaround - in real scenario would use Request object
    # For now, we'll accept both cookie and body
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
    )

    # Try to get from body (for testing/SPA)
    # In production: refresh token should ONLY be in httpOnly cookie
    # This endpoint should be called with credentials include by frontend
    # FastAPI will automatically send cookies if request.credentials = "include"

    # For now, we need a workaround since we can't directly access cookies in dependency
    # The refresh token might be passed in Authorization header for SPA
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use POST /api/auth/refresh with cookie",
    )


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
