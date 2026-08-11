"""
PDF text extraction utility.

Unlike the other tools in this folder, this isn't exposed to the LLM as a
tool-call — it runs once, synchronously, when a PDF is uploaded, and the
extracted text is injected directly into the conversation as context. This
keeps the agent loop simple: by the time the model sees the question, the
PDF content is just plain text sitting in the system prompt.
"""

import logging

from pypdf import PdfReader

logger = logging.getLogger(__name__)

# Hard cap so an enormous PDF can't blow up the context window / token cost.
_MAX_CHARS = 20_000


def extract_text(file_bytes: bytes) -> dict:
    """
    Extract text from PDF bytes.

    Returns a dict rather than raising, so a corrupt/unreadable PDF is a
    normal error result the caller can show to the user, not a 500 crash.
    """
    try:
        reader = PdfReader(file_bytes if hasattr(file_bytes, "read") else __import__("io").BytesIO(file_bytes))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to open PDF: %s", exc)
        return {"error": f"Could not read this PDF: {exc}"}

    if reader.is_encrypted:
        return {"error": "This PDF is password-protected and cannot be read."}

    pages_text = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to extract a page: %s", exc)
            continue

    full_text = "\n\n".join(pages_text).strip()

    if not full_text:
        return {"error": "No extractable text found (this may be a scanned/image-only PDF)."}

    truncated = len(full_text) > _MAX_CHARS
    return {
        "text": full_text[:_MAX_CHARS],
        "truncated": truncated,
        "page_count": len(reader.pages),
    }