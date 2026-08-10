"""
Image generation tool using Pollinations.ai — a free, keyless image API.
Pollinations serves an image directly from a GET request to a URL built
from the prompt, so "generating" an image here just means building that
URL correctly. No API key, no signup, no cost.
"""

from typing import Any
from urllib.parse import quote

TOOL_SCHEMA: dict[str, Any] = {
    "name": "generate_image",
    "description": (
        "Generate an image from a text description. Use this ONLY when the "
        "user explicitly asks for an image, picture, drawing, or illustration "
        "to be created — not for research questions."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "A clear, descriptive prompt for the image to generate.",
            }
        },
        "required": ["prompt"],
    },
}


async def run(prompt: str) -> dict[str, Any]:
    if not prompt or not prompt.strip():
        return {"error": "Empty prompt provided."}

    encoded = quote(prompt.strip())
    image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=768&nologo=true"

    return {"image_url": image_url, "prompt": prompt}