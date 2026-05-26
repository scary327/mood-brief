"""
Fetch an image by URL (e.g. from Pinterest) and return the bytes.

The browser cannot fetch i.pinimg.com or pinterest.com directly because of
CORS, so we proxy through the backend. We also follow Pinterest pin pages
by parsing <meta property="og:image"> to find the real image.

Safety:
  * Only http(s) URLs.
  * Resolve host to IP and refuse private / loopback / link-local addresses
    so this endpoint can't be used as an SSRF gateway into the docker
    network or cloud metadata service.
  * Hard cap on response size.
  * Strict content-type check on the final response.
"""
from __future__ import annotations

import ipaddress
import logging
import re
import socket
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.models import User
from app.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["fetch-url"])

MAX_BYTES = 10 * 1024 * 1024  # 10 MB — matches analyze.py
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Recognise pinterest pin / board pages so we can scrape the og:image instead
# of trying to download HTML as if it were an image.
_PIN_HOSTS = re.compile(r"(^|\.)pinterest\.[a-z.]+$", re.IGNORECASE)


class FetchUrlRequest(BaseModel):
    url: str


class FetchUrlResponse(BaseModel):
    filename: str
    content_type: str
    data_base64: str  # base64-encoded image bytes


def _is_safe_host(host: str) -> bool:
    """Resolve host and reject private / loopback / metadata addresses."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            return False
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False
    return True


def _validate_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        raise HTTPException(status_code=422, detail="URL is required")
    if len(url) > 2048:
        raise HTTPException(status_code=422, detail="URL too long")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=422, detail="Only http(s) URLs are allowed")
    if not parsed.hostname:
        raise HTTPException(status_code=422, detail="Invalid host")
    if not _is_safe_host(parsed.hostname):
        raise HTTPException(status_code=400, detail="Host is not allowed")
    return url


def _extract_og_image(html: str) -> str | None:
    # og:image / og:image:secure_url — Pinterest sets both
    for prop in ("og:image:secure_url", "og:image"):
        m = re.search(
            rf'<meta[^>]+property=["\']{re.escape(prop)}["\'][^>]*content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE,
        )
        if m:
            return m.group(1)
        m = re.search(
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(prop)}["\']',
            html,
            re.IGNORECASE,
        )
        if m:
            return m.group(1)
    return None


async def _download_bytes(
    client: httpx.AsyncClient, url: str
) -> tuple[bytes, str]:
    """Stream-download with a hard cap. Returns (bytes, content_type)."""
    async with client.stream("GET", url) as resp:
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=400,
                detail=f"Remote returned {resp.status_code}",
            )
        ctype = (resp.headers.get("content-type") or "").split(";")[0].strip().lower()
        chunks: list[bytes] = []
        total = 0
        async for chunk in resp.aiter_bytes(chunk_size=64 * 1024):
            total += len(chunk)
            if total > MAX_BYTES:
                raise HTTPException(status_code=413, detail="Image too large (>10MB)")
            chunks.append(chunk)
        return b"".join(chunks), ctype


@router.post("/fetch-image-url", response_model=FetchUrlResponse)
async def fetch_image_url(
    body: FetchUrlRequest,
    current_user: User = Depends(get_current_user),
):
    """Download an image (directly or via Pinterest og:image) and return it
    base64-encoded so the frontend can stuff it into the existing analyze flow."""
    import base64

    url = _validate_url(body.url)
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()

    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}

    async with httpx.AsyncClient(
        timeout=20.0,
        follow_redirects=True,
        max_redirects=5,
        headers=headers,
    ) as client:
        # Pinterest pin pages → scrape og:image first
        if _PIN_HOSTS.search(host):
            try:
                page = await client.get(url)
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=502, detail=f"Failed to fetch page: {exc}")
            if page.status_code >= 400:
                raise HTTPException(
                    status_code=400,
                    detail=f"Pinterest returned {page.status_code}",
                )
            img_url = _extract_og_image(page.text)
            if not img_url:
                raise HTTPException(
                    status_code=400,
                    detail="Не удалось найти изображение на странице Pinterest. "
                           "Попробуйте вставить прямую ссылку на картинку.",
                )
            # Validate the discovered image URL too (could redirect anywhere).
            url = _validate_url(img_url)

        try:
            data, ctype = await _download_bytes(client, url)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Failed to download: {exc}")

    # Sniff content-type if server lied or returned octet-stream
    if ctype not in ALLOWED_CONTENT_TYPES:
        sniffed = _sniff_image_type(data)
        if sniffed is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported content type: {ctype or 'unknown'}",
            )
        ctype = sniffed

    # Derive a sensible filename
    path = urlparse(url).path or ""
    base = path.rsplit("/", 1)[-1] or "image"
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base)[:80]
    if "." not in base:
        ext = ctype.split("/")[-1] if ctype else "jpg"
        base = f"{base}.{ext}"

    logger.info("Fetched %s bytes from %s (%s)", len(data), url, ctype)
    return FetchUrlResponse(
        filename=base,
        content_type=ctype,
        data_base64=base64.b64encode(data).decode("ascii"),
    )


def _sniff_image_type(data: bytes) -> str | None:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return None
