from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


PAYLOADS = [
    {
        "tenant_id": "clinic-demo",
        "session_id": "dash-seed-001",
        "user_id": "seed-user-001",
        "user_text": "Tenho uma mancha na pele, coçando. Posso usar corticoide?",
        "extract_mode": "heuristic",
        "top_k": 3
    },
    {
        "tenant_id": "clinic-demo",
        "session_id": "dash-seed-002",
        "user_id": "seed-user-002",
        "user_text": "Qual o horário de funcionamento da clínica?",
        "extract_mode": "heuristic",
        "top_k": 3
    },
    {
        "tenant_id": "clinic-demo",
        "session_id": "dash-seed-003",
        "user_id": "seed-user-003",
        "user_text": "Posso?",
        "extract_mode": "heuristic",
        "top_k": 3
    }
]


def main() -> None:
    for payload in PAYLOADS:
        response = client.post("/agent/chat", json=payload)
        print(response.status_code, response.json().get("action_taken"), response.json().get("evaluation_id"))


if __name__ == "__main__":
    main()
