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
