from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rag_search_returns_context():
    response = client.post(
        "/rag/search",
        json={
            "tenant_id": "clinic-demo",
            "query": "pomada corticoide pele coceira",
            "top_k": 2
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["results"]
    assert any("clínica" in item["title"].lower() or "política" in item["title"].lower() for item in body["results"])
