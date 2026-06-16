from fastapi.testclient import TestClient

from app.main import app
from app.extraction.models import NormativeFacts

client = TestClient(app)


def test_fact_schema_endpoint():
    response = client.get("/extract/schema")
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0.0"
    assert "json_schema" in body
    assert "properties" in body["json_schema"]


def test_heuristic_extraction_health_medication():
    payload = {
        "tenant_id": "clinic-demo",
        "session_id": "extract-test-001",
        "user_id": "user-001",
        "user_text": "Tenho uma mancha na pele. Posso usar corticoide?",
        "mode": "heuristic",
        "low_confidence_threshold": 0.70,
        "enqueue_human_review_on_fallback": True
    }

    response = client.post("/extract/facts", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["valid"] is True
    assert body["requires_human_review"] is False
    assert body["facts"]["domain"] == "healthcare"
    assert body["facts"]["request_type"] == "clinical_recommendation"
    assert body["facts"]["mentions_medication"] is True


def test_low_confidence_fallback_creates_human_review():
    payload = {
        "tenant_id": "clinic-demo",
        "session_id": "extract-test-002",
        "user_id": "user-002",
        "user_text": "Posso?",
        "mode": "heuristic",
        "low_confidence_threshold": 0.70,
        "enqueue_human_review_on_fallback": True
    }

    response = client.post("/extract/facts", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["requires_human_review"] is True
    assert body["fallback_reason"] == "low_fact_extraction_confidence"
    assert body["review_id"]

    pending = client.get("/human-review/pending")
    assert pending.status_code == 200
    assert any(item["review_id"] == body["review_id"] for item in pending.json()["items"])


def test_mock_llm_extraction_returns_raw_output():
    payload = {
        "tenant_id": "clinic-demo",
        "user_text": "Estou com febre alta e dor intensa. O que faço?",
        "mode": "llm_mock",
        "low_confidence_threshold": 0.70,
        "enqueue_human_review_on_fallback": False
    }

    response = client.post("/extract/facts", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["mode"] == "llm_mock"
    assert body["raw_model_output"]
    assert body["facts"]["has_urgent_symptoms"] is True
    assert body["facts"]["domain"] == "healthcare"


def test_normative_facts_schema_validates_confidence_range():
    schema = NormativeFacts.model_json_schema()
    assert schema["properties"]["fact_extraction_confidence"]["minimum"] == 0.0
    assert schema["properties"]["fact_extraction_confidence"]["maximum"] == 1.0
