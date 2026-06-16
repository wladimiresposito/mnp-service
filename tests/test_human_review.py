from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_resolve_human_review_item():
    payload = {
        "tenant_id": "clinic-demo",
        "session_id": "review-test-001",
        "user_id": "user-review",
        "user_text": "Pode?",
        "mode": "heuristic",
        "low_confidence_threshold": 0.70,
        "enqueue_human_review_on_fallback": True
    }

    extraction = client.post("/extract/facts", json=payload)
    assert extraction.status_code == 200
    review_id = extraction.json()["review_id"]
    assert review_id

    resolution = client.post(
        f"/human-review/{review_id}/resolve",
        json={
            "resolution": {
                "approved_facts": {
                    "domain": "general",
                    "request_type": "unknown",
                    "fact_extraction_confidence": 0.95
                },
                "reviewer": "test"
            }
        }
    )

    assert resolution.status_code == 200
    assert resolution.json()["status"] == "resolved"

    fetched = client.get(f"/human-review/{review_id}")
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "resolved"
