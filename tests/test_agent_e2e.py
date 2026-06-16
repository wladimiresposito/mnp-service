# Copyright 2026 Wladimir Esposito (OmniAI / Omni Tech Consulting)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_agent_health_medication_is_modified_and_audited():
    payload = {
        "tenant_id": "clinic-demo",
        "session_id": "agent-test-001",
        "user_id": "user-agent-001",
        "user_text": "Tenho uma mancha na pele, coçando. Posso usar corticoide?",
        "extract_mode": "heuristic",
        "top_k": 3,
        "allow_tool_calls": True,
        "enqueue_human_review_on_fallback": True
    }

    response = client.post("/agent/chat", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["action_taken"] == "modified"
    assert body["verdict"]["decision"] == "modify"
    assert body["evaluation_id"]
    assert "Não consigo avaliar" in body["final_answer"]
    assert body["retrieved_context"]

    audit = client.get(f"/audit/{body['evaluation_id']}")
    assert audit.status_code == 200
    assert audit.json()["id"] == body["evaluation_id"]


def test_agent_admin_question_is_answered():
    payload = {
        "tenant_id": "clinic-demo",
        "session_id": "agent-test-002",
        "user_id": "user-agent-002",
        "user_text": "Qual o horário de funcionamento da clínica?",
        "extract_mode": "heuristic",
        "top_k": 3,
        "allow_tool_calls": True,
        "enqueue_human_review_on_fallback": True
    }

    response = client.post("/agent/chat", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["action_taken"] == "answered"
    assert body["verdict"]["decision"] == "allow"
    assert "segunda" in body["final_answer"].lower()


def test_agent_low_confidence_short_circuits_to_human_review():
    payload = {
        "tenant_id": "clinic-demo",
        "session_id": "agent-test-003",
        "user_id": "user-agent-003",
        "user_text": "Posso?",
        "extract_mode": "heuristic",
        "top_k": 3,
        "allow_tool_calls": True,
        "enqueue_human_review_on_fallback": True
    }

    response = client.post("/agent/chat", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["action_taken"] == "escalated"
    assert body["review_id"]
    assert body["extraction"]["requires_human_review"] is True
    assert "revisão humana" in body["final_answer"].lower()


def test_agent_requesting_disabled_plugin_returns_400():
    payload = {
        "tenant_id": "legal-demo",
        "session_id": "agent-test-004",
        "user_id": "user-agent-004",
        "user_text": "Tenho uma mancha na pele. Posso usar corticoide?",
        "plugins": ["medical_safety_simplified"],
        "extract_mode": "heuristic"
    }

    response = client.post("/agent/chat", json=payload)
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"]
