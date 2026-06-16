from __future__ import annotations

import json
import re
import time
import urllib.request
from typing import Any

from app.config.settings import settings
from app.extraction.base import FactExtractor
from app.extraction.heuristic_extractor import HeuristicFactExtractor
from app.extraction.models import NormativeFacts
from app.extraction.prompt import SYSTEM_PROMPT, build_user_prompt


class LLMExtractionError(RuntimeError):
    pass


class MockLLMFactExtractor(FactExtractor):
    """
    Deterministic mock that simulates an LLM returning schema-conformant JSON.
    Useful for local tests and demos without external API calls.
    """

    mode = "llm_mock"

    def extract(self, user_text: str) -> tuple[NormativeFacts, str | None]:
        facts, _ = HeuristicFactExtractor(default_confidence=0.86).extract(user_text)
        raw = facts.model_dump_json()
        return facts, raw


class OpenAICompatibleFactExtractor(FactExtractor):
    """
    Minimal OpenAI-compatible adapter using Python stdlib.

    It expects a /chat/completions endpoint and a model that can return JSON.
    This is intentionally simple for MVP v0.5; production should add retries,
    telemetry, circuit breaker, provider-specific JSON mode and token limits.
    """

    mode = "openai_compatible"

    def extract(self, user_text: str) -> tuple[NormativeFacts, str | None]:
        if not settings.llm_base_url:
            raise LLMExtractionError("MNP_LLM_BASE_URL is required for openai_compatible mode.")

        payload = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(user_text)},
            ],
            "temperature": 0,
            # Pede JSON estrito quando o provedor suporta. Provedores que
            # ignoram o campo apenas o descartam; o parser tolera markdown.
            "response_format": {"type": "json_object"},
        }

        url = settings.llm_base_url.rstrip("/") + "/chat/completions"
        body = json.dumps(payload).encode("utf-8")

        # Retry com backoff para falhas transitorias de rede/provedor.
        attempts = max(1, settings.llm_max_retries + 1)
        last_exc: Exception | None = None
        for attempt in range(attempts):
            request = urllib.request.Request(
                url, data=body, method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.llm_api_key}",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=settings.llm_timeout_seconds) as response:
                    raw_response = response.read().decode("utf-8")
                break
            except Exception as exc:  # transitorio: tenta de novo
                last_exc = exc
                if attempt < attempts - 1:
                    time.sleep(settings.llm_retry_backoff_seconds * (2 ** attempt))
        else:
            raise LLMExtractionError(f"LLM extraction call failed after {attempts} attempts: {last_exc}")

        try:
            data = json.loads(raw_response)
            content = data["choices"][0]["message"]["content"]
            json_text = _extract_json_object(content)
            facts = NormativeFacts.model_validate_json(json_text)
            return facts, content
        except Exception as exc:
            raise LLMExtractionError(f"Could not parse LLM extraction output: {exc}") from exc


def _extract_json_object(text: str) -> str:
    """
    Accepts raw JSON or JSON fenced in markdown. Returns the first JSON object.
    """
    stripped = text.strip()
    if stripped.startswith("{"):
        return stripped

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL)
    if fenced:
        return fenced.group(1)

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        return stripped[start:end + 1]

    raise ValueError("No JSON object found in LLM output.")
