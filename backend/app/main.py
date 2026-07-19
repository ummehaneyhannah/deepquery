"""
FastAPI entrypoint. Kept intentionally thin — all real logic lives in
app.agent.core. This file's only job is HTTP plumbing: request validation,
routing, and error translation.
"""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agent.core import ResearchAgent
from app.config import settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title="DeepQuery API", version="0.1.0")

# CORS open for local dev; tighten allow_origins before deploying publicly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_agent = ResearchAgent()


class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)


class ResearchResponse(BaseModel):
    answer: str
    iterations_used: int
    sources_fetched: list[str]
    stopped_reason: str


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest) -> ResearchResponse:
    try:
        result = await _agent.run(request.question)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Agent run failed")
        raise HTTPException(status_code=500, detail="Agent failed to complete research.") from exc

    return ResearchResponse(
        answer=result.answer,
        iterations_used=result.iterations_used,
        sources_fetched=result.sources_fetched,
        stopped_reason=result.stopped_reason,
    )