"""OCR engine abstraction (design section 6.4 / FR-17).

Uses Tesseract via ``pytesseract`` when both the Python package and the native
binary are available. Otherwise it degrades gracefully so the platform remains
fully runnable in constrained/free-tier environments:

  * If a ``.txt`` sidecar file exists next to the image (or the uploaded file is
    itself text), its contents are used as the "extracted" text.
  * Otherwise a clear placeholder is returned and the pipeline continues.

This keeps the Phase 2 workflow demonstrable end-to-end without heavy native
dependencies, while remaining a drop-in for real OCR in production.
"""
from __future__ import annotations

from pathlib import Path

_TEXT_SUFFIXES = {".txt", ".md"}


def _try_tesseract(path: Path) -> str | None:
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except Exception:
        return None
    try:
        return pytesseract.image_to_string(Image.open(path)).strip()
    except Exception:
        # Native binary missing or unreadable image.
        return None


def extract_text(path: Path | None) -> tuple[str, str]:
    """Return ``(text, engine)`` extracted from an image/file path.

    ``engine`` identifies which backend produced the text, useful for auditing.
    """
    if path is None or not path.exists():
        return "", "none"

    if path.suffix.lower() in _TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8", errors="ignore").strip(), "text"

    # Sidecar transcript support for demos without a real OCR binary.
    sidecar = path.with_suffix(path.suffix + ".txt")
    if sidecar.exists():
        return sidecar.read_text(encoding="utf-8", errors="ignore").strip(), "sidecar"

    text = _try_tesseract(path)
    if text:
        return text, "tesseract"

    return (
        "[OCR unavailable: no text could be extracted from the uploaded image. "
        "Install Tesseract or provide a .txt transcript to enable extraction.]",
        "fallback",
    )
