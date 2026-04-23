import httpx

from optimus_backend.core.provider.base import LLMProvider


class GroqProvider:
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant") -> None:
        self.api_key = api_key
        self.model = model
        self._base_url = "https://api.groq.com/openai/v1/chat/completions"

    async def complete(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1024,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
