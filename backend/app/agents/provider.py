"""
LLM provider abstraction. OpenRouter (serving openai/gpt-5-mini) is the
primary and only provider for the MVP — multi-provider fallback is explicitly
Nice-to-Have / deferred (see docs/ROADMAP.md). Isolating the SDK call here is
what makes agents/copilot.py's ReAct loop testable with a fake provider,
independent of any real API call.
"""
from typing import Any

from openai import AsyncOpenAI

from app.core.config import get_settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class LLMProvider:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        settings = get_settings()
        self._client = AsyncOpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=api_key or settings.openrouter_api_key,
        )
        self._model = model or settings.openrouter_model

    async def create_message(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 2000,
    ):
        return await self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[{"role": "system", "content": system}, *messages],
            tools=tools or None,
        )
    