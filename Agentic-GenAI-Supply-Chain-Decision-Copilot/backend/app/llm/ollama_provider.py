import json
import logging
from typing import Optional, Type, TypeVar
import httpx
from pydantic import BaseModel

from app.llm.provider import LLMProvider
from app.config.settings import settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class OllamaProvider(LLMProvider):
    """
    LLM Provider implementation for local Ollama server.
    Interacts via HTTP REST API (e.g. http://localhost:11434).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.LLM_MODEL
        self.timeout = timeout

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        url = f"{self.base_url}/api/chat"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "").strip()
        except httpx.ConnectError:
            msg = f"Ollama service unavailable at {self.base_url}. Ensure Ollama is running (`ollama serve`)."
            logger.error(msg)
            raise RuntimeError(msg)
        except Exception as e:
            msg = f"Ollama generation failed: {str(e)}"
            logger.error(msg)
            raise RuntimeError(msg)

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_prompt: Optional[str] = None
    ) -> T:
        schema_json = json.dumps(response_schema.model_json_schema())
        augmented_system = (
            (system_prompt or "") +
            f"\n\nReturn ONLY a valid JSON object matching the following Pydantic JSON Schema:\n{schema_json}"
        ).strip()

        url = f"{self.base_url}/api/chat"
        messages = [
            {"role": "system", "content": augmented_system},
            {"role": "user", "content": prompt}
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "format": "json",
            "stream": False
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                raw_json = data.get("message", {}).get("content", "").strip()

                try:
                    return response_schema.model_validate_json(raw_json)
                except Exception as parse_err:
                    logger.warning(f"Ollama output validation failed: {parse_err}. Attempting repair...")
                    clean_json = raw_json.strip("`").removeprefix("json").strip()
                    return response_schema.model_validate_json(clean_json)

        except httpx.ConnectError:
            msg = f"Ollama service unavailable at {self.base_url}."
            logger.error(msg)
            raise RuntimeError(msg)
        except Exception as e:
            msg = f"Ollama structured generation failed: {str(e)}"
            logger.error(msg)
            raise RuntimeError(msg)
