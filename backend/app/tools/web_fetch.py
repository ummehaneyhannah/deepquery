"""
Web fetch tool — reads a specific URL's full content.

Search snippets are too short for real synthesis (a 2-line summary can't
support a well-cited claim). This tool fetches the actual page so the
agent can read the full argument before quoting or paraphrasing it.
"""

import logging
import re
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

TOOL_SCHEMA: dict[str, Any] = {
    "name": "web_fetch",
    "description": (
        "Fetch the full text content of a specific URL. Use this after "
        "web_search to read a promising source in full before citing it."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The absolute URL to fetch."}
        },
        "required": ["url"],
    },
}

# Hard cap on characters returned to the model — keeps token spend bounded
# even if a page is enormous. The agent should ask for a narrower fetch
# (e.g. a different URL/section) rather than get an unbounded context dump.
_MAX_CHARS = 2_000

_TAG_RE = re.compile(r"<script.*?</script>|<style.*?</style>", re.DOTALL | re.IGNORECASE)
_ALL_TAGS_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\n{3,}")


def _strip_html(html: str) -> str:
    """Minimal HTML-to-text fallback when no richer parser is available."""
    text = _TAG_RE.sub(" ", html)
    text = _ALL_TAGS_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub("\n\n", text)
    return text.strip()


async def run(url: str) -> dict[str, Any]:
    if not url or not url.startswith(("http://", "https://")):
        return {"error": "Invalid URL — must be an absolute http(s) URL.", "url": url}

    try:
        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.warning("Fetch failed for %s: HTTP %s", url, exc.response.status_code)
        return {"error": f"HTTP {exc.response.status_code} fetching URL.", "url": url}
    except httpx.RequestError as exc:
        logger.warning("Fetch request error for %s: %s", url, exc)
        return {"error": "Network/timeout error fetching URL.", "url": url}

    content_type = response.headers.get("content-type", "")
    if "text/html" in content_type:
        text = _strip_html(response.text)
    else:
        text = response.text

    truncated = len(text) > _MAX_CHARS
    return {
        "url": url,
        "content": text[:_MAX_CHARS],
        "truncated": truncated,
    }