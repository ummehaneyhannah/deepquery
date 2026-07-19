"""
Web search tool — the agent's primary way of discovering sources.

Uses Tavily because it's purpose-built for LLM agents: it returns cleaned,
pre-summarized snippets instead of raw SERP HTML, which means fewer tokens
spent on parsing junk and a lower hallucination surface.
"""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

TAVILY_ENDPOINT = "https://api.tavily.com/search"

# JSON schema exposed to Claude so it knows how to call this tool.
TOOL_SCHEMA: dict[str, Any] = {
    "name": "web_search",
    "description": (
        "Search the live web for a query and return relevant results with "
        "titles, URLs, and content snippets. Use this to discover sources "
        "before reading them in full with web_fetch."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "A short, specific search query (3-8 words works best).",
            }
        },
        "required": ["query"],
    },
}


async def run(query: str) -> dict[str, Any]:
    """
    Execute a search and return a normalized result set.

    Returns a dict rather than raising on empty results — an empty result
    set is a valid outcome the agent should reason about (e.g. try a
    different query), not a crash.
    """
    if not query or not query.strip():
        return {"error": "Empty query provided.", "results": []}

    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "max_results": settings.max_sources_per_query,
        "include_answer": False,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.post(TAVILY_ENDPOINT, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("Tavily returned HTTP %s for query %r", exc.response.status_code, query)
        return {"error": f"Search provider error: {exc.response.status_code}", "results": []}
    except httpx.RequestError as exc:
        logger.warning("Tavily request failed for query %r: %s", query, exc)
        return {"error": "Search request failed (network/timeout).", "results": []}

    results = [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", ""),
        }
        for item in data.get("results", [])
    ]
    return {"query": query, "results": results}