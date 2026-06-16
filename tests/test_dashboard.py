from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_html_loads():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "MNP Operational Dashboard" in response.text
    assert "/metrics/summary" in response.text
    assert "/audit" in response.text
    assert "/human-review/pending" in response.text


def test_dashboard_data_endpoints_work_after_seed():
    payload = {
        "tenant_id": "clinic-demo",
        "session_id": "dashboard-test-001",
        "user_id": "dashboard-user",
        "user_text": "Tenho uma mancha na pele. Posso usar corticoide?",
        "extract_mode": "heuristic",
        "top_k": 3
    }

    created = client.post("/agent/chat", json=payload)
    assert created.status_code == 200

    summary = client.get("/metrics/summary", params={"tenant_id": "clinic-demo"})
    assert summary.status_code == 200
    assert summary.json()["total_evaluations"] >= 1

    audit = client.get("/audit", params={"tenant_id": "clinic-demo", "limit": 5})
    assert audit.status_code == 200
    assert audit.json()["items"]

    rules = client.get("/metrics/rules", params={"tenant_id": "clinic-demo"})
    assert rules.status_code == 200
    assert "rules" in rules.json()
