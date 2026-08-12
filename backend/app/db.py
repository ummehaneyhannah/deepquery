"""
Persistent storage for conversation history and PDF chunks, backed by
Supabase (Postgres). Replaces the in-memory dicts that previously reset
whenever the server restarted or the free-tier instance spun down.

Kept intentionally simple: two tables, each keyed by conversation_id,
storing a JSON blob. No ORM — a few small functions are enough for this
access pattern (get-by-id, upsert-by-id).
"""

import logging

from supabase import Client, create_client

from app.config import settings

logger = logging.getLogger(__name__)

_client: Client = create_client(settings.supabase_url, settings.supabase_key)


def get_history(conversation_id: str) -> list[dict]:
    """Return stored message history for a conversation, or [] if none exists."""
    try:
        result = (
            _client.table("conversations")
            .select("history")
            .eq("conversation_id", conversation_id)
            .execute()
        )
        if result.data:
            return result.data[0]["history"]
        return []
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load history for %s: %s", conversation_id, exc)
        return []


def save_history(conversation_id: str, history: list[dict]) -> None:
    """Upsert the full message history for a conversation."""
    try:
        _client.table("conversations").upsert(
            {"conversation_id": conversation_id, "history": history}
        ).execute()
    except Exception as exc:  # noqa: BLE001
        # Storage failing shouldn't break the user's current answer — just
        # means this turn's history won't persist for next time.
        logger.warning("Failed to save history for %s: %s", conversation_id, exc)


def get_pdf_chunks(conversation_id: str) -> list[str] | None:
    """Return stored PDF chunks for a conversation, or None if none exist."""
    try:
        result = (
            _client.table("pdf_chunks")
            .select("chunks")
            .eq("conversation_id", conversation_id)
            .execute()
        )
        if result.data:
            return result.data[0]["chunks"]
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load PDF chunks for %s: %s", conversation_id, exc)
        return None


def save_pdf_chunks(conversation_id: str, chunks: list[str]) -> None:
    """Upsert PDF chunks for a conversation."""
    try:
        _client.table("pdf_chunks").upsert(
            {"conversation_id": conversation_id, "chunks": chunks}
        ).execute()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to save PDF chunks for %s: %s", conversation_id, exc)