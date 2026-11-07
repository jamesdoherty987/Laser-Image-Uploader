"""Cheap AI image edits via Gemini (preferred) or OpenAI."""

from __future__ import annotations

import base64
import json
import logging
from io import BytesIO

import httpx
from fastapi import HTTPException, status
from PIL import Image

from app.core.config import Settings

logger = logging.getLogger(__name__)

LASER_EDIT_HINT = (
    "Apply only the requested edit to this photo. "
    "Preserve the main subject, composition, and proportions. "
    "Do not add text or watermarks. Return the edited image."
)


def _to_png_bytes(data: bytes) -> tuple[bytes, str]:
    with Image.open(BytesIO(data)) as image:
        image = image.convert("RGB")
        # Keep edits manageable for cheap image models
        longest = max(image.size)
        if longest > 1536:
            scale = 1536 / longest
            image = image.resize(
                (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
                Image.Resampling.LANCZOS,
            )
        buf = BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue(), "image/png"


def _gemini_error_detail(status_code: int, body_text: str) -> str:
    """Turn Gemini HTTP errors into a short user-facing message."""
    message = ""
    try:
        payload = json.loads(body_text)
        err = payload.get("error") if isinstance(payload, dict) else None
        if isinstance(err, dict):
            message = str(err.get("message") or "")
    except json.JSONDecodeError:
        message = ""
    lower = message.lower()
    if status_code == 429 or "quota" in lower or "rate" in lower:
        return (
            "Gemini image quota exceeded (free tier for image models is often 0). "
            "Enable billing in Google AI Studio, or set OPENAI_API_KEY as a fallback."
        )
    if status_code in {401, 403} or "api key" in lower or "permission" in lower:
        return "Gemini rejected the API key. Check GEMINI_API_KEY in backend/.env."
    if status_code == 404 or "not found" in lower:
        return f"Gemini model not found. Check GEMINI_IMAGE_MODEL ({message[:160] or '404'})."
    if message:
        return f"Gemini image edit failed: {message[:220]}"
    return "Gemini image edit failed. Check GEMINI_API_KEY / model name."


def _extract_gemini_image(body: dict) -> bytes:
    """Pull image bytes from a Gemini generateContent response, or raise a clear error."""
    candidates = body.get("candidates") or []
    if not candidates:
        feedback = body.get("promptFeedback") or {}
        reason = feedback.get("blockReason") or "unknown"
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini blocked this prompt ({reason}). Try a different photo or edit.",
        )

    candidate = candidates[0] if isinstance(candidates[0], dict) else {}
    finish = str(candidate.get("finishReason") or "")
    finish_message = str(candidate.get("finishMessage") or "")
    content = candidate.get("content") or {}
    parts = content.get("parts") or []

    for part in parts:
        if not isinstance(part, dict):
            continue
        inline = part.get("inlineData") or part.get("inline_data")
        if not isinstance(inline, dict):
            continue
        data = inline.get("data")
        if data:
            return base64.b64decode(data)

    # Common with celebrity / real-person photos: image generated then filtered
    if finish in {"IMAGE_OTHER", "IMAGE_SAFETY", "IMAGE_PROHIBITED_CONTENT", "SAFETY"}:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Gemini refused to return an edited image for this photo "
                "(common with celebrity / real-person likeness filters). "
                "Try a non-celebrity photo, a simpler prompt like "
                "“remove the background”, or use OpenAI instead."
            ),
        )

    if finish_message:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini returned no image: {finish_message[:240]}",
        )

    text_bits = [
        str(part.get("text"))
        for part in parts
        if isinstance(part, dict) and part.get("text")
    ]
    if text_bits:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini returned text only: {text_bits[0][:200]}",
        )

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Gemini returned no image.",
    )


def edit_with_gemini(settings: Settings, image_bytes: bytes, prompt: str) -> bytes:
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GEMINI_API_KEY is not configured.",
        )

    png_bytes, mime = _to_png_bytes(image_bytes)
    model = settings.gemini_image_model
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    full_prompt = f"{prompt.strip()}\n\n{LASER_EDIT_HINT}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": full_prompt},
                    {
                        "inline_data": {
                            "mime_type": mime,
                            "data": base64.b64encode(png_bytes).decode("ascii"),
                        }
                    },
                ],
            }
        ],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
        },
    }
    # Prefer header auth so the key is not printed in httpx URL access logs
    headers = {"x-goog-api-key": settings.gemini_api_key}

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        logger.exception("Gemini request failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Gemini.",
        ) from exc

    if response.status_code >= 400:
        logger.error("Gemini error %s: %s", response.status_code, response.text[:400])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_gemini_error_detail(response.status_code, response.text),
        )

    body = response.json()
    try:
        return _extract_gemini_image(body)
    except HTTPException:
        finish = ""
        try:
            finish = str((body.get("candidates") or [{}])[0].get("finishReason") or "")
        except Exception:  # noqa: BLE001
            finish = ""
        logger.warning("Gemini edit produced no image (finishReason=%s)", finish or "?")
        raise


def edit_with_openai(settings: Settings, image_bytes: bytes, prompt: str) -> bytes:
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OPENAI_API_KEY is not configured.",
        )

    png_bytes, _ = _to_png_bytes(image_bytes)
    # Images API edit (gpt-image / dall-e compatible multipart)
    model = settings.image_edit_model or "gpt-image-1"
    url = "https://api.openai.com/v1/images/edits"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    files = {
        "image": ("image.png", png_bytes, "image/png"),
    }
    data = {
        "model": model,
        "prompt": f"{prompt.strip()}\n\n{LASER_EDIT_HINT}",
        "n": "1",
        "size": "1024x1024",
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers, data=data, files=files)
    except httpx.HTTPError as exc:
        logger.exception("OpenAI request failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach OpenAI.",
        ) from exc

    if response.status_code >= 400:
        logger.error("OpenAI error %s: %s", response.status_code, response.text[:500])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI image edit failed. Check OPENAI_API_KEY / model.",
        )

    body = response.json()
    try:
        item = body["data"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI returned no image.",
        ) from exc

    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    if item.get("url"):
        with httpx.Client(timeout=60.0) as client:
            downloaded = client.get(item["url"])
            downloaded.raise_for_status()
            return downloaded.content

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="OpenAI returned an unexpected image payload.",
    )


def edit_image(settings: Settings, image_bytes: bytes, prompt: str) -> bytes:
    prompt = (prompt or "").strip()
    if len(prompt) < 3:
        raise HTTPException(status_code=400, detail="Enter a short edit prompt.")

    provider = (settings.image_edit_provider or "gemini").lower()
    if provider == "openai":
        return edit_with_openai(settings, image_bytes, prompt)
    if provider == "gemini":
        return edit_with_gemini(settings, image_bytes, prompt)

    # Auto: prefer Gemini when keyed, else OpenAI
    if settings.gemini_api_key:
        return edit_with_gemini(settings, image_bytes, prompt)
    if settings.openai_api_key:
        return edit_with_openai(settings, image_bytes, prompt)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Set GEMINI_API_KEY (recommended, cheaper) or OPENAI_API_KEY in backend/.env",
    )
