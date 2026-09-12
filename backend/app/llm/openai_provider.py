import os
import json
import logging
from typing import Optional, Type, TypeVar
import httpx
from pydantic import BaseModel

from app.llm.provider import LLMProvider
from app.config.settings import settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(LLMProvider):
    """
    LLM Provider implementation for OpenAI and OpenAI-compatible Chat Completions APIs.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: float = 30.0
    ):
        self.api_key = api_key or settings.LLM_API_KEY or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _get_headers(self) -> dict:
        if not self.api_key:
            raise RuntimeError("OpenAI API key not configured. Set LLM_API_KEY or OPENAI_API_KEY in environment.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        headers = self._get_headers()
        url = f"{self.base_url}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            msg = f"OpenAI generation failed: {str(e)}"
            logger.error(msg)
            raise RuntimeError(msg)

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_prompt: Optional[str] = None
    ) -> T:
        headers = self._get_headers()
        url = f"{self.base_url}/chat/completions"
        schema_json = json.dumps(response_schema.model_json_schema())
        augmented_system = (
            (system_prompt or "") +
            f"\n\nReturn ONLY a valid JSON object matching the following Pydantic JSON Schema:\n{schema_json}"
        ).strip()

        messages = [
            {"role": "system", "content": augmented_system},
            {"role": "user", "content": prompt}
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                raw_json = data["choices"][0]["message"]["content"].strip()
                return response_schema.model_validate_json(raw_json)
        except Exception as e:
            msg = f"OpenAI structured generation failed: {str(e)}"
            logger.error(msg)
            raise RuntimeError(msg)
