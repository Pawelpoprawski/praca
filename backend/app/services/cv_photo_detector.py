"""Detect whether a CV file (PDF or DOCX) contains a portrait photo of the candidate.

Strategy:
1. Extract embedded raster images from the file.
2. Filter out tiny icons / huge files / clearly non-photo bytes.
3. Ask the vision model in a single call: 'is any of these a portrait photo?'.
4. Return True / False / None (None when we cannot decide — e.g. extraction failed).
"""
from __future__ import annotations

import base64
import logging
from typing import Iterable

from app.config import get_settings

logger = logging.getLogger(__name__)

MIN_IMAGE_BYTES = 4 * 1024        # skip icons / tiny decorations
MAX_IMAGE_BYTES = 4 * 1024 * 1024  # skip huge backgrounds
MAX_IMAGES_TO_SEND = 4             # bound the vision payload


def _iter_pdf_images(file_path: str) -> Iterable[tuple[bytes, str]]:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        for page in reader.pages:
            try:
                images = page.images
            except Exception:
                continue
            for img in images:
                try:
                    data = img.data
                    name = (img.name or "").lower()
                except Exception:
                    continue
                if not data:
                    continue
                ext = "png"
                if name.endswith(".jpg") or name.endswith(".jpeg"):
                    ext = "jpeg"
                elif name.endswith(".png"):
                    ext = "png"
                elif data[:3] == b"\xff\xd8\xff":
                    ext = "jpeg"
                elif data[:8] == b"\x89PNG\r\n\x1a\n":
                    ext = "png"
                yield data, ext
    except Exception as e:
        logger.warning(f"PDF image extraction failed: {e}")


def _iter_docx_images(file_path: str) -> Iterable[tuple[bytes, str]]:
    try:
        from docx import Document
        doc = Document(file_path)
        for rel in doc.part.related_parts.values():
            try:
                ct = (rel.content_type or "").lower()
            except Exception:
                continue
            if "image" not in ct:
                continue
            try:
                data = rel.blob
            except Exception:
                continue
            if not data:
                continue
            if "jpeg" in ct or "jpg" in ct:
                ext = "jpeg"
            elif "png" in ct:
                ext = "png"
            elif data[:3] == b"\xff\xd8\xff":
                ext = "jpeg"
            elif data[:8] == b"\x89PNG\r\n\x1a\n":
                ext = "png"
            else:
                continue
            yield data, ext
    except Exception as e:
        logger.warning(f"DOCX image extraction failed: {e}")


def _collect_candidate_images(file_path: str, mime_type: str) -> list[tuple[bytes, str]]:
    if mime_type == "application/pdf":
        raw = list(_iter_pdf_images(file_path))
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        raw = list(_iter_docx_images(file_path))
    else:
        return []

    filtered: list[tuple[bytes, str]] = []
    for data, ext in raw:
        if len(data) < MIN_IMAGE_BYTES:
            continue
        if len(data) > MAX_IMAGE_BYTES:
            continue
        filtered.append((data, ext))

    filtered.sort(key=lambda x: len(x[0]), reverse=True)
    return filtered[:MAX_IMAGES_TO_SEND]


async def detect_photo(file_path: str, mime_type: str) -> bool | None:
    """Returns True if a portrait photo of a person is in the file, False if no such image,
    or None if we cannot decide (no API key, extraction failed, no candidates were sent etc.)."""
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        return None

    images = _collect_candidate_images(file_path, mime_type)
    if not images:
        return False

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        content: list[dict] = [
            {
                "type": "text",
                "text": (
                    "Otrzymujesz obrazy wyciagniete z pliku CV. "
                    "Odpowiedz JEDNYM SLOWEM: 'TAK' jesli ktorykolwiek z nich to portretowe "
                    "zdjecie tworzy / osoby (twarz kandydata, popiersie, naturalne ujecie). "
                    "'NIE' jesli to wylacznie logo, ikony, ozdobniki, mapy, wykresy, ramki, "
                    "tla, podpisy lub inne nieportretowe grafiki. Tylko 'TAK' lub 'NIE'."
                ),
            }
        ]
        for data, ext in images:
            b64 = base64.b64encode(data).decode("ascii")
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/{ext};base64,{b64}", "detail": "low"},
            })

        response = await client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": "Odpowiadasz wylacznie 'TAK' albo 'NIE'."},
                {"role": "user", "content": content},
            ],
            max_completion_tokens=4,
        )
        ans = (response.choices[0].message.content or "").strip().upper()
        if ans.startswith("TAK"):
            return True
        if ans.startswith("NIE"):
            return False
        return None
    except Exception as e:
        logger.warning(f"Vision photo detection failed: {e}")
        return None
