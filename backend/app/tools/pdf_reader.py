"""
PDF text extraction + lightweight (TF-IDF) retrieval.

Why TF-IDF instead of neural embeddings: neural embedding models
(sentence-transformers etc.) require ~500MB+ of dependencies and enough
RAM to load them, which risks crashing on free-tier hosting (Render's
free instances have 512MB RAM). TF-IDF is a classic sparse-vector
retrieval method — no model download, pure math, runs reliably anywhere.
It's a real, valid RAG approach (this is how search engines worked for
decades before neural embeddings) — just keyword/term-frequency-based
rather than semantic. Good enough to make "ask questions about a large
PDF" actually work without loading the whole document into every prompt.
"""

import io
import logging
import re

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

_CHUNK_WORDS = 400  # ~500-600 tokens per chunk, a reasonable retrieval unit
_TOP_K = 3  # how many chunks to hand the agent per question


def extract_text(file_bytes: bytes) -> dict:
    """Extract raw text from PDF bytes, split into per-page text."""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
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

    return {"text": full_text, "page_count": len(reader.pages)}


def chunk_text(text: str) -> list[str]:
    """Split text into ~_CHUNK_WORDS-word chunks on whitespace boundaries."""
    words = re.split(r"\s+", text.strip())
    chunks = []
    for i in range(0, len(words), _CHUNK_WORDS):
        chunk = " ".join(words[i : i + _CHUNK_WORDS])
        if chunk:
            chunks.append(chunk)
    return chunks


def retrieve_relevant_chunks(chunks: list[str], query: str, top_k: int = _TOP_K) -> list[str]:
    """
    Return the top_k chunks most relevant to the query, using TF-IDF +
    cosine similarity. Falls back to returning the first chunks if the
    document is too short/uniform for TF-IDF to meaningfully rank.
    """
    if len(chunks) <= top_k:
        return chunks

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        chunk_vectors = vectorizer.fit_transform(chunks)
        query_vector = vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, chunk_vectors)[0]

        ranked_indices = similarities.argsort()[::-1][:top_k]
        # Preserve original document order among the selected chunks so
        # the retrieved context still reads coherently.
        ranked_indices = sorted(ranked_indices)
        return [chunks[i] for i in ranked_indices]
    except Exception as exc:  # noqa: BLE001
        logger.warning("TF-IDF retrieval failed, falling back to first chunks: %s", exc)
        return chunks[:top_k]