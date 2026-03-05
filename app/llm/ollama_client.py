from __future__ import annotations
from dataclasses import dataclass
import httpx

@dataclass
class OllamaClient:
    base_url: str
    model: str
    timeout_s: int = 30

    async def generate(self, prompt: str) -> str:
        url = f"{self.base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": 450,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                r = await client.post(url, json=payload)
                r.raise_for_status()
                data = r.json()
                return (data.get("response") or "").strip()
        except httpx.TimeoutException as e:
            raise TimeoutError("LLM timeout") from e
