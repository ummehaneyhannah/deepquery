"""
Persistent storage for conversation history and PDF chunks, backed by
Supabase (Postgres). Replaces the in-memory dicts that previously reset
whenever the server restarted or the free-tier instance spun down.

Kept intentionally simple: two tables, each keyed by conversation_id,
storing a JSON blob. No ORM — a few small functions are enough for this
access pattern (get-by-id, upsert-by-id).

History round-tripping: our agent stores assistant turns as lists of
TextBlock/ToolUseBlock dataclasses, which aren't JSON-serializable as-is.
_to_jsonable() flattens them to plain dicts before saving; _from_jsonable()
reconstructs the dataclasses when loading, so the agent loop sees exactly
the same shape it would have from an in-memory session.
"""

import logging
from dataclasses import asdict, is_dataclass

from supabase import Client, create_client

from app.config import settings
from app.llm_client import TextBlock, ToolUseBlock

logger = logging.getLogger(__name__)

_client: Client = create_client(settings.supabase_url, settings.supabase_key)


def _to_jsonable(obj):
    """Recursively convert dataclasses (TextBlock/ToolUseBlock) into plain
    JSON-serializable dicts, so history can be stored as JSONB."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if isinstance(obj, list):
        return [_to_jsonable(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    return obj


def _from_jsonable(history: list[dict]) -> list[dict]:
    """Reverse of _to_jsonable for assistant turns: rebuild TextBlock/
    ToolUseBlock dataclass instances from the plain dicts Supabase returns,
    so the agent loop sees the same objects it would from an in-memory run."""
    rebuilt = []
    for msg in history:
        content = msg.get("content")
        if msg.get("role") == "assistant" and isinstance(content, list):
            blocks = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    blocks.append(TextBlock(**block))
                elif isinstance(block, dict) and block.get("type") == "tool_use":
                    blocks.append(ToolUseBlock(**block))
                else:
                    blocks.append(block)
            rebuilt.append({**msg, "content": blocks})
        else:
            rebuilt.append(msg)
    return rebuilt


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
            return _from_jsonable(result.data[0]["history"])
        return []
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load history for %s: %s", conversation_id, exc)
        return []


def save_history(conversation_id: str, history: list[dict]) -> None:
    """Upsert the full message history for a conversation."""
    try:
        _client.table("conversations").upsert(
            {"conversation_id": conversation_id, "history": _to_jsonable(history)}
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