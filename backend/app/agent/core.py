"""
The ResearchAgent: the reasoning loop that turns a question into a
sourced answer.

Design notes (why it's built this way):
- The loop is bounded (max_agent_iterations) so a confused agent can't
  burn API credits forever — it must converge or explicitly give up.
- Every tool result is fed back verbatim so the model can judge source
  quality itself; we don't pre-filter or pre-summarize search results
  before the model sees them, since that would hide information the
  model needs to reason about reliability.
- Citations are enforced structurally: the system prompt requires the
  final answer to reference source URLs, and we track which URLs were
  actually fetched so we can flag ungrounded claims later if needed.
"""

import json
import logging
from dataclasses import dataclass, field

from app.config import settings
from app.llm_client import LLMClient
from app.tools import web_fetch, web_search

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a careful research agent. Given a research question:

1. Break it into sub-questions if it's broad.
2. Use web_search to find candidate sources. Prefer specific, narrow queries \
over broad ones — run multiple searches rather than one vague one.
3. Use web_fetch to read the full content of ONE promising source before \
writing your final answer. Do not fetch more than one source - keep the \
research tight and efficient. Only fetch a URL that was literally returned \
in a web_search result you have already seen - never invent a URL yourself.
4. If a fetch fails (error in the tool result), do not retry the same URL — \
move on to a different source instead.
5. If early results conflict or seem thin, search again with a refined \
query rather than settling for the first answer.
6. When you have enough grounded information, STOP calling tools and write \
a final answer in plain text. Every non-obvious claim must reference the \
URL that supports it, e.g. "(source: https://...)".
7. If you cannot find reliable information after reasonable effort, say so \
plainly rather than guessing.

Be concise. Do not pad the answer with restated questions or filler."""

TOOLS = [web_search.TOOL_SCHEMA, web_fetch.TOOL_SCHEMA]

_TOOL_DISPATCH = {
    "web_search": web_search.run,
    "web_fetch": web_fetch.run,
}


@dataclass
class AgentResult:
    answer: str
    iterations_used: int
    sources_fetched: list[str] = field(default_factory=list)
    stopped_reason: str = "completed"  # "completed" | "max_iterations"


class ResearchAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client or LLMClient()

    async def run(self, question: str) -> AgentResult:
        messages: list[dict] = [{"role": "user", "content": question}]
        sources_fetched: list[str] = []

        for iteration in range(1, settings.max_agent_iterations + 1):
            response = self._llm.create_message(
                messages=messages,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
            )

            # Model may respond with tool calls, text, or both in one turn.
            tool_uses = [block for block in response.content if block.type == "tool_use"]

            if not tool_uses:
                # No more tools requested — treat text content as the final answer.
                final_text = "".join(
                    block.text for block in response.content if block.type == "text"
                )
                return AgentResult(
                    answer=final_text,
                    iterations_used=iteration,
                    sources_fetched=sources_fetched,
                    stopped_reason="completed",
                )

            # Append the assistant turn, then execute every requested tool
            # and append their results before looping back to the model.
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for tool_use in tool_uses:
                result = await self._execute_tool(tool_use.name, tool_use.input)
                if tool_use.name == "web_fetch" and "url" in tool_use.input and "error" not in result:
                    sources_fetched.append(tool_use.input["url"])
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "name": tool_use.name,
                        "content": json.dumps(result),
                    }
                )
            messages.append({"role": "user", "content": tool_results})

        # Loop exhausted without a final answer — surface partial progress
        # rather than raising, so the caller can still show something useful.
        logger.warning("Agent hit max_iterations (%d) without concluding.", settings.max_agent_iterations)
        return AgentResult(
            answer=(
                "I wasn't able to reach a confident conclusion within the "
                "allotted research steps. Here is what I found so far, "
                f"drawing on {len(sources_fetched)} source(s): "
                + ", ".join(sources_fetched)
            ),
            iterations_used=settings.max_agent_iterations,
            sources_fetched=sources_fetched,
            stopped_reason="max_iterations",
        )

    @staticmethod
    async def _execute_tool(name: str, tool_input: dict) -> dict:
        handler = _TOOL_DISPATCH.get(name)
        if handler is None:
            return {"error": f"Unknown tool: {name}"}
        try:
            return await handler(**tool_input)
        except Exception as exc:  # noqa: BLE001 - tool failures must not crash the loop
            logger.exception("Tool %s failed", name)
            return {"error": f"Tool execution failed: {exc}"}