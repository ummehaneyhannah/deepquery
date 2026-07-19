"""
Groq-backed LLM client (OpenAI-compatible chat completions API), kept
interface-compatible with the previous wrappers: create_message returns
an object with a `.content` list of TextBlock/ToolUseBlock instances,
so app.agent.core does not need to change.
"""

import json
import logging
from dataclasses import dataclass

from groq import BadRequestError, Groq
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_fixed

from app.config import settings

logger = logging.getLogger(__name__)

_client = Groq(api_key=settings.groq_api_key)


@dataclass
class TextBlock:
    type: str
    text: str


@dataclass
class ToolUseBlock:
    type: str
    id: str
    name: str
    input: dict


class _Response:
    def __init__(self, content):
        self.content = content


def _convert_tools(tools):
    if not tools:
        return None
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        }
        for t in tools
    ]


def _to_openai_messages(messages, system):
    """Flatten our generic block-based message list into OpenAI's format."""
    openai_messages = [{"role": "system", "content": system}]

    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if isinstance(content, str):
            openai_messages.append({"role": role, "content": content})
            continue

        if role == "assistant":
            text_parts = [b.text for b in content if isinstance(b, TextBlock)]
            tool_calls = [
                {
                    "id": b.id,
                    "type": "function",
                    "function": {"name": b.name, "arguments": json.dumps(b.input)},
                }
                for b in content
                if isinstance(b, ToolUseBlock)
            ]
            entry = {"role": "assistant", "content": " ".join(text_parts) or None}
            if tool_calls:
                entry["tool_calls"] = tool_calls
            openai_messages.append(entry)
        else:
            # user turn carrying tool_result dicts
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    openai_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": block["tool_use_id"],
                            "content": block["content"],
                        }
                    )
    return openai_messages


def _to_response(completion) -> _Response:
    message = completion.choices[0].message
    blocks = []
    if message.content:
        blocks.append(TextBlock(type="text", text=message.content))
    for tc in message.tool_calls or []:
        blocks.append(
            ToolUseBlock(
                type="tool_use",
                id=tc.id,
                name=tc.function.name,
                input=json.loads(tc.function.arguments),
            )
        )
    return _Response(blocks)

def _is_malformed_tool_call(exc: BaseException) -> bool:
    """
    Llama models on Groq occasionally emit a malformed tool-call token
    (e.g. `<function=...>` instead of valid JSON). This is intermittent,
    not a real bad request from us, so it's worth an automatic retry
    rather than surfacing it as a hard failure straight away.
    """
    return isinstance(exc, BadRequestError) and "tool_use_failed" in str(exc)


class LLMClient:
    @retry(
        retry=retry_if_exception(_is_malformed_tool_call),
        wait=wait_fixed(1),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def create_message(self, messages, system, tools=None, max_tokens=4096):
        openai_messages = _to_openai_messages(messages, system)
        completion = _client.chat.completions.create(
            model=settings.groq_model,
            messages=openai_messages,
            tools=_convert_tools(tools),
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return _to_response(completion)
