"""Exercita o caminho OpenAI-compatible sem endpoint real.

A licao do bug do ASP: um caminho sem teste e um caminho quebrado. Aqui
mockamos urllib para cobrir parse de JSON puro, JSON em markdown, retry em
falha transitoria e degradacao graciosa quando o LLM falha de vez.
"""
import io
import json

import pytest

from app.config.settings import settings
from app.extraction import llm_extractor as mod
from app.extraction.llm_extractor import LLMExtractionError, OpenAICompatibleFactExtractor
from app.extraction.models import FactExtractionRequest
from app.extraction.service import extract_and_validate


def _fake_response(content: str):
    body = json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")

    class _Ctx:
        def __enter__(self_inner):
            return io.BytesIO(body)

        def __exit__(self_inner, *a):
            return False

    return _Ctx()


VALID_JSON = json.dumps({
    "domain": "healthcare",
    "request_type": "clinical_recommendation",
    "contains_sensitive_health_data": True,
    "mentions_medication": True,
    "fact_extraction_confidence": 0.88,
})


@pytest.fixture(autouse=True)
def _configure_llm(monkeypatch):
    monkeypatch.setattr(settings, "llm_base_url", "http://fake-llm.local/v1")
    monkeypatch.setattr(settings, "llm_max_retries", 2)
    monkeypatch.setattr(settings, "llm_retry_backoff_seconds", 0.0)


def test_openai_compatible_parses_plain_json(monkeypatch):
    monkeypatch.setattr(mod.urllib.request, "urlopen",
                        lambda *a, **k: _fake_response(VALID_JSON))
    facts, raw = OpenAICompatibleFactExtractor().extract("mancha na pele")
    assert facts.domain == "healthcare"
    assert facts.contains_sensitive_health_data is True


def test_openai_compatible_parses_markdown_fenced_json(monkeypatch):
    fenced = f"```json\n{VALID_JSON}\n```"
    monkeypatch.setattr(mod.urllib.request, "urlopen",
                        lambda *a, **k: _fake_response(fenced))
    facts, _ = OpenAICompatibleFactExtractor().extract("mancha na pele")
    assert facts.domain == "healthcare"


def test_openai_compatible_retries_then_succeeds(monkeypatch):
    calls = {"n": 0}

    def flaky(*a, **k):
        calls["n"] += 1
        if calls["n"] < 2:
            raise OSError("connection reset")
        return _fake_response(VALID_JSON)

    monkeypatch.setattr(mod.urllib.request, "urlopen", flaky)
    facts, _ = OpenAICompatibleFactExtractor().extract("mancha na pele")
    assert facts.domain == "healthcare"
    assert calls["n"] == 2  # falhou uma vez, sucesso na segunda


def test_openai_compatible_raises_after_exhausting_retries(monkeypatch):
    def always_fail(*a, **k):
        raise OSError("unreachable")

    monkeypatch.setattr(mod.urllib.request, "urlopen", always_fail)
    with pytest.raises(LLMExtractionError):
        OpenAICompatibleFactExtractor().extract("x")


def test_service_degrades_to_human_review_when_llm_fails(monkeypatch):
    def always_fail(*a, **k):
        raise OSError("unreachable")

    monkeypatch.setattr(mod.urllib.request, "urlopen", always_fail)
    resp = extract_and_validate(FactExtractionRequest(
        user_text="mancha na pele",
        mode="openai_compatible",
        enqueue_human_review_on_fallback=False,
    ))
    # Degradacao graciosa: nao crasha, escala para revisao humana.
    assert resp.requires_human_review is True
    assert resp.facts.fact_extraction_confidence == 0.0
