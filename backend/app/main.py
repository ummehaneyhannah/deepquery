"""
FastAPI entrypoint. Kept intentionally thin — all real logic lives in
app.agent.core. This file's only job is HTTP plumbing: request validation,
routing, and error translation.

Conversation history is kept in an in-memory dict keyed by conversation_id.
This is intentionally simple (no database) for now — it resets whenever
the server restarts or the free-tier instance spins down from inactivity.
A persistent store (e.g. a database) can replace this dict later without
changing the API shape.
"""

import logging
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agent.core import ResearchAgent
from app.config import settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title="DeepQuery API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_agent = ResearchAgent()

# conversation_id -> list of message dicts (the agent's internal format)
_conversations: dict[str, list[dict]] = {}


class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    conversation_id: str | None = None


class ResearchResponse(BaseModel):
    answer: str
    iterations_used: int
    sources_fetched: list[str]
    stopped_reason: str
    conversation_id: str
    image_url: str | None = None


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest) -> ResearchResponse:
    conversation_id = request.conversation_id or str(uuid.uuid4())
    history = _conversations.get(conversation_id, [])

    try:
        result = await _agent.run(request.question, history=history)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Agent run failed")
        raise HTTPException(status_code=500, detail="Agent failed to complete research.") from exc

    _conversations[conversation_id] = result.updated_history

    return ResearchResponse(
        answer=result.answer,
        iterations_used=result.iterations_used,
        sources_fetched=result.sources_fetched,
        stopped_reason=result.stopped_reason,
        conversation_id=conversation_id,
        image_url=result.image_url,
    )

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str) -> dict:
    _conversations.pop(conversation_id, None)
    return {"deleted": conversation_id}