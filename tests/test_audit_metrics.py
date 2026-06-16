from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_evaluation():
    payload = {
        "tenant_id": "clinic-demo",
        "session_id": "audit-test-session",
        "user_id": "audit-user",
        "context": {
            "tenant_id": "clinic-demo",
            "session_id": "audit-test-session",
            "user_id": "audit-user",
            "user_text": "Tenho uma mancha na pele. Posso usar corticoide?",
            "facts": {
                "domain": "healthcare",
                "contains_sensitive_health_data": True,
                "request_type": "clinical_recommendation",
                "mentions_medication": True,
                "legal_basis_confirmed": False,
                "fact_extraction_confidence": 0.83
            }
        },
        "draft": {
            "text": "Pode usar a pomada com corticoide. É seguro usar.",
            "facts": {
                "domain": "healthcare",
                "contains_sensitive_health_data": True,
                "request_type": "clinical_recommendation",
                "mentions_medication": True
            },
            "confidence": 0.82
        }
    }
    response = client.post("/evaluate/all", json=payload)
    assert response.status_code == 200
    return response.json()["evaluation_id"]


def test_audit_get_and_list():
    evaluation_id = _create_evaluation()

    detail = client.get(f"/audit/{evaluation_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == evaluation_id

    listed = client.get("/audit", params={"tenant_id": "clinic-demo", "limit": 10})
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1
    assert any(item["id"] == evaluation_id for item in listed.json()["items"])


def test_audit_by_session():
    evaluation_id = _create_evaluation()

    response = client.get("/audit/by-session/audit-test-session")
    assert response.status_code == 200
    assert response.json()["total"] >= 1
    assert any(item["id"] == evaluation_id for item in response.json()["items"])


def test_metrics_endpoints():
    _create_evaluation()

    summary = client.get("/metrics/summary", params={"tenant_id": "clinic-demo"})
    assert summary.status_code == 200
    assert summary.json()["total_evaluations"] >= 1

    rules = client.get("/metrics/rules", params={"tenant_id": "clinic-demo"})
    assert rules.status_code == 200
    assert "rules" in rules.json()

    plugins = client.get("/metrics/plugins", params={"tenant_id": "clinic-demo"})
    assert plugins.status_code == 200
    assert "plugins" in plugins.json()
