"""
Shared OpenRouter HTTP client with automatic model fallback.

Iterates through a chain of models. On retryable errors (network failure,
timeout, 429, 403, 5xx) moves to the next model. On the first success,
returns the parsed JSON. If every model fails, raises HTTPException with
the last observed error.
"""
import logging
from typing import Any

import httpx
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

# Statuses that mean "this model is unavailable right now — try another"
_RETRYABLE_STATUSES = {403, 408, 409, 429, 500, 502, 503, 504, 520, 522, 524}


def _build_headers() -> dict[str, str]:
    api_key = (settings.OPENROUTER_API_KEY or "").strip().strip('"').strip("'")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.OPENROUTER_REFERER,
        "X-Title": settings.OPENROUTER_TITLE,
    }


def _extract_error(resp: httpx.Response) -> str:
    try:
        body = resp.json()
        return (
            body.get("error", {}).get("message")
            or body.get("message")
            or resp.text[:400]
        )
    except Exception:
        return resp.text[:400] or f"HTTP {resp.status_code}"


async def chat_completion_with_fallback(
    payload: dict[str, Any],
    models: list[str],
    timeout: float = 120.0,
) -> tuple[dict[str, Any], str]:
    """
    Try each model in `models` in order. Return (response_json, model_used)
    on the first success.

    Raises HTTPException only after every model has failed, or immediately
    on a non-retryable error such as 400 (bad payload) or 401 (bad API key).
    """
    if not models:
        raise HTTPException(status_code=500, detail="Не задан ни один OpenRouter-модель")

    if not settings.OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY is not set")

    headers = _build_headers()
    last_status: int | None = None
    last_detail: str = ""

    async with httpx.AsyncClient(timeout=timeout) as client:
        for idx, model in enumerate(models):
            payload["model"] = model
            label = f"[{idx + 1}/{len(models)}] {model}"
            try:
                resp = await client.post(
                    f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                )
            except (httpx.TimeoutException, httpx.RequestError) as exc:
                last_detail = f"network error: {exc!r}"
                last_status = None
                logger.warning("OpenRouter %s failed (%s) — falling back", label, last_detail)
                continue

            if resp.is_success:
                if idx > 0:
                    logger.info("OpenRouter fallback succeeded with %s", label)
                return resp.json(), model

            last_status = resp.status_code
            last_detail = _extract_error(resp)

            if resp.status_code in _RETRYABLE_STATUSES:
                logger.warning(
                    "OpenRouter %s returned %s: %s — falling back",
                    label, resp.status_code, last_detail[:200],
                )
                continue

            logger.error(
                "OpenRouter %s returned non-retryable %s: %s",
                label, resp.status_code, last_detail[:200],
            )
            break

    if last_status == 400:
        raise HTTPException(
            status_code=400,
            detail=f"OpenRouter отклонил запрос (400): {last_detail}",
        )
    if last_status == 401:
        raise HTTPException(
            status_code=502,
            detail="Неверный API-ключ OpenRouter. Проверьте настройки.",
        )
    if last_status == 402:
        raise HTTPException(
            status_code=402,
            detail="Недостаточно средств на счёте OpenRouter.",
        )
    if last_status == 413:
        raise HTTPException(
            status_code=413,
            detail="Изображение слишком большое. Уменьшите его до 4 МБ или меньше.",
        )

    raise HTTPException(
        status_code=502,
        detail=(
            f"Все доступные модели OpenRouter не ответили "
            f"(перебрано {len(models)}). Последняя ошибка: {last_detail or 'неизвестно'}"
        ),
    )
