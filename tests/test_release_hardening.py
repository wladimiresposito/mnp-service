from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_system_version():
    response = client.get("/system/version")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "1.0.0"
    assert body["service"] == "mnp-service"


def test_system_live_and_ready():
    live = client.get("/system/live")
    assert live.status_code == 200
    assert live.json()["status"] == "live"

    ready = client.get("/system/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] in {"ready", "degraded"}
    assert "checks" in ready.json()


def test_request_id_and_security_headers():
    response = client.get("/health", headers={"X-Request-ID": "test-request-id"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-id"
    assert "X-Process-Time-ms" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_request_body_too_large_guard():
    response = client.post(
        "/extract/facts",
        headers={"content-length": "999999999"},
        json={"tenant_id": "clinic-demo", "user_text": "teste"},
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "Request body too large."
