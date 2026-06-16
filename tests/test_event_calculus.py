from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_event_calculus_status_endpoint():
    response = client.get("/event-calculus/status")
    assert response.status_code == 200
    body = response.json()
    assert body["plugin_id"] == "lgpd_event_calculus"
    assert "10_event_calculus.lp" in body["modules"]


def test_event_calculus_active_consent_allows():
    payload = {
        "subject": "user-123",
        "purpose": "process_health_data_for_pre_anamnesis",
        "current_time": 10,
        "data_category": "health",
        "events": [
            {
                "t": 1,
                "kind": "grant_consent",
                "subject": "user-123",
                "purpose": "process_health_data_for_pre_anamnesis"
            }
        ],
        "requires_legal_basis": True,
        "requires_purpose_confirmation": True
    }

    response = client.post("/event-calculus/evaluate", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["decision"]["allowed"] is True
    assert body["decision"]["forbidden"] is False
    assert any(f["fluent"].startswith("consent(") and f["holds"] is True for f in body["fluents"])


def test_event_calculus_revoked_consent_forbids_and_clips():
    payload = {
        "subject": "user-123",
        "purpose": "process_health_data_for_pre_anamnesis",
        "current_time": 10,
        "data_category": "health",
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
        ],
        "requires_legal_basis": True,
        "requires_purpose_confirmation": True
    }

    response = client.post("/event-calculus/evaluate", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["decision"]["allowed"] is False
    assert body["decision"]["forbidden"] is True
    assert "ec_sensitive_processing_without_active_consent" in body["decision"]["violated_rules"]
    assert "obtain_active_consent" in body["decision"]["required_changes"]

    consent_fluent = next(f for f in body["fluents"] if f["fluent"].startswith("consent("))
    assert consent_fluent["holds"] is False
    assert consent_fluent["clipped_by"]


def test_event_calculus_breach_adds_obligation_and_consequence():
    payload = {
        "subject": "user-123",
        "purpose": "process_health_data_for_pre_anamnesis",
        "current_time": 10,
        "data_category": "health",
        "events": [
            {
                "t": 1,
                "kind": "grant_consent",
                "subject": "user-123",
                "purpose": "process_health_data_for_pre_anamnesis"
            },
            {
                "t": 8,
                "kind": "data_breach",
                "subject": "user-123",
                "purpose": "process_health_data_for_pre_anamnesis"
            }
        ],
        "requires_legal_basis": True,
        "requires_purpose_confirmation": True
    }

    response = client.post("/event-calculus/evaluate", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["decision"]["allowed"] is True
    assert body["decision"]["risk_level"] == "critical"
    obligation_ids = {o["obligation_id"] for o in body["decision"]["obligations"]}
    consequence_ids = {c["consequence_id"] for c in body["decision"]["consequences"]}
    assert "obl_log_and_notify_breach" in obligation_ids
    assert "cons_breach_response_required" in consequence_ids


def test_lgpd_event_calculus_plugin_revoked_consent_escalates_or_modifies():
    payload = {
        "context": {
            "tenant_id": "clinic-ec-demo",
            "session_id": "ec-test-001",
            "user_id": "user-123",
            "user_text": "Tenho uma mancha na pele e quero fazer uma pré-anamnese.",
            "facts": {
                "domain": "healthcare",
                "contains_sensitive_health_data": True,
                "request_type": "general_information",
                "purpose": "process_health_data_for_pre_anamnesis",
                "current_time": 10,
                "data_category": "health",
                "ec_events": [
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
        }
    }

    response = client.post("/evaluate/input", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["tenant_id"] == "clinic-ec-demo"
    assert body["active_plugins"] == ["lgpd_event_calculus"]
    assert body["verdict"]["decision"] in {"modify", "escalate"}
    assert "ec_sensitive_processing_without_active_consent" in body["verdict"]["violated_rules"]


def test_lgpd_event_calculus_plugin_active_consent_allows():
    payload = {
        "context": {
            "tenant_id": "clinic-ec-demo",
            "session_id": "ec-test-002",
            "user_id": "user-123",
            "user_text": "Tenho uma mancha na pele e quero fazer uma pré-anamnese.",
            "facts": {
                "domain": "healthcare",
                "contains_sensitive_health_data": True,
                "request_type": "general_information",
                "purpose": "process_health_data_for_pre_anamnesis",
                "current_time": 10,
                "data_category": "health",
                "ec_events": [
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
