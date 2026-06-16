from fastapi.testclient import TestClient

from app.main import app
from app.asp.engine import clingo_available

client = TestClient(app)


def test_asp_status_endpoint():
    response = client.get("/asp/status")
    assert response.status_code == 200
    body = response.json()
    assert "clingo_available" in body
    assert body["plugin_id"] == "lgpd_temporal_asp"


def test_temporal_consent_active_allows():
    payload = {
        "subject": "user-123",
        "purpose": "process_health_data_for_pre_anamnesis",
        "current_time": 10,
        "sensitive_health_data": True,
        "events": [
            {
                "t": 1,
                "kind": "grant_consent",
                "subject": "user-123",
                "purpose": "process_health_data_for_pre_anamnesis"
            }
        ]
    }

    response = client.post("/asp/temporal-consent", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["allowed"] is True
    assert body["active_consent"] is True
    assert body["forbidden"] is False


def test_temporal_consent_revoked_forbids():
    payload = {
        "subject": "user-123",
        "purpose": "process_health_data_for_pre_anamnesis",
        "current_time": 10,
        "sensitive_health_data": True,
        "events": [
            {
                "t": 1,
                "kind": "grant_consent",
                "subject": "user-123",
                "purpose": "process_health_data_for_pre_anamnesis"
            },
            {
                "t": 5,
                "kind": "revoke_consent",
                "subject": "user-123",
                "purpose": "process_health_data_for_pre_anamnesis"
            }
        ]
    }

    response = client.post("/asp/temporal-consent", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["allowed"] is False
    assert body["active_consent"] is False
    assert body["forbidden"] is True
    assert "obtain_active_consent" in body["required_changes"]


def test_lgpd_temporal_asp_plugin_no_consent_modifies():
    payload = {
        "context": {
            "tenant_id": "clinic-asp-demo",
            "session_id": "asp-test-001",
            "user_id": "user-123",
            "user_text": "Tenho uma mancha na pele e quero fazer uma pré-anamnese.",
            "facts": {
                "domain": "healthcare",
                "contains_sensitive_health_data": True,
                "request_type": "general_information",
                "purpose": "process_health_data_for_pre_anamnesis",
                "current_time": 10,
                "temporal_events": []
            }
        }
    }

    response = client.post("/evaluate/input", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == "clinic-asp-demo"
    assert body["active_plugins"] == ["lgpd_temporal_asp"]
    assert body["verdict"]["decision"] == "modify"
    assert "temporal_sensitive_health_processing_without_active_consent" in body["verdict"]["violated_rules"]


def test_lgpd_temporal_asp_plugin_active_consent_allows():
    payload = {
        "context": {
            "tenant_id": "clinic-asp-demo",
            "session_id": "asp-test-002",
            "user_id": "user-123",
            "user_text": "Tenho uma mancha na pele e quero fazer uma pré-anamnese.",
            "facts": {
                "domain": "healthcare",
                "contains_sensitive_health_data": True,
                "request_type": "general_information",
                "purpose": "process_health_data_for_pre_anamnesis",
                "current_time": 10,
                "temporal_events": [
                    {
                        "t": 1,
                        "kind": "grant_consent",
                        "subject": "user-123",
                        "purpose": "process_health_data_for_pre_anamnesis"
                    }
                ]
            }
        }
    }

    response = client.post("/evaluate/input", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"]["decision"] == "allow"
    assert body["verdict"]["risk_level"] == "low"
