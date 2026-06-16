import json
import logging
import re
import time
from functools import lru_cache

from app.config import settings

logger = logging.getLogger(__name__)


class LLM:
    def complete(self, system: str, user: str) -> str:
        raise NotImplementedError

    def complete_json(self, system: str, user: str, schema_hint: str = "") -> dict:
        json_system = (
            system
            + "\n\nRespond with valid JSON only. No prose, no markdown fences, no explanation."
        )
        if schema_hint:
            json_system += f"\n\nExpected JSON shape: {schema_hint}"

        for attempt in range(2):
            raw = self.complete(json_system, user)
            raw = raw.strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            try:
                return json.loads(raw)
            except json.JSONDecodeError as e:
                if attempt == 0:
                    logger.warning("JSON parse failed, retrying: %s", e)
                    continue
                logger.error("JSON parse failed after retry. Raw:\n%s", raw[:500])
                raise ValueError(f"LLM did not return valid JSON: {e}") from e
        return {}


class _GeminiLLM(LLM):
    def __init__(self):
        from google import genai
        from google.genai import types
        self._client = genai.Client(api_key=settings.google_api_key)
        self._types = types
        self._model = settings.gemini_model

    def complete(self, system: str, user: str) -> str:
        for attempt in range(3):
            try:
                resp = self._client.models.generate_content(
                    model=self._model,
                    contents=user,
                    config=self._types.GenerateContentConfig(
                        system_instruction=system,
                        max_output_tokens=8192,
                    ),
                )
                return resp.text
            except Exception as e:
                msg = str(e)
                if ("429" in msg or "RESOURCE_EXHAUSTED" in msg) and attempt < 2:
                    # second retry needs more breathing room than the first
                    wait = 60 if attempt else 30
                    logger.warning("Gemini rate limited, retry %d in %ds", attempt + 1, wait)
                    time.sleep(wait)
                    continue
                raise


class _GroqLLM(LLM):
    def __init__(self):
        from groq import Groq
        self._client = Groq(api_key=settings.groq_api_key)
        self._model = settings.groq_model

    def complete(self, system: str, user: str) -> str:
        for attempt in range(2):
            try:
                resp = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    max_tokens=8192,
                )
                return resp.choices[0].message.content
            except Exception as e:
                msg = str(e)
                if ("429" in msg or "rate_limit" in msg.lower()) and attempt == 0:
                    logger.warning("Groq rate limited, retrying in 15s")
                    time.sleep(15)
                    continue
                raise


class _FallbackLLM(LLM):
    def __init__(self, primary: LLM, fallback: LLM):
        self._primary = primary
        self._fallback = fallback

    def complete(self, system: str, user: str) -> str:
        try:
            return self._primary.complete(system, user)
        except Exception as e:
            msg = str(e)
            if "429" in msg or "rate_limit" in msg.lower() or "RESOURCE_EXHAUSTED" in msg:
                logger.warning("Primary LLM rate limited, switching to fallback")
                return self._fallback.complete(system, user)
            raise


@lru_cache(maxsize=1)
def get_llm() -> LLM:
    provider = settings.llm_provider.lower()
    if provider == "gemini":
        return _GeminiLLM()
    if provider == "groq":
        primary = _GroqLLM()
        if settings.google_api_key:
            return _FallbackLLM(primary, _GeminiLLM())
        return primary
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}. Use 'gemini' or 'groq'.")
