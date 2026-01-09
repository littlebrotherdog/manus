"""HTTP based OpenAI-compatible LLM client."""

from __future__ import annotations

import httpx

from .base import ChatCompletion, ChatMessage, LLMClient

class HttpLLMClient(LLMClient):
    def __init__(self, *, base_url: str, api_key: str, timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def chat(
        self,
        messages,
        *,
        temperature: float,
        max_tokens: int,
        model: str,
    ) -> ChatCompletion:
        payload = {
            "model": model,
            "messages": [m.__dict__ for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        choice = data["choices"][0]["message"]
        content = choice.get("content") or ""
        return ChatCompletion(content=content, raw=data)
