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


def test_evaluate_output_modify():
    payload = {
        "tenant_id": "clinic-demo",
        "draft": {
            "text": "Pode usar a pomada com corticoide. É seguro usar.",
            "facts": {
                "domain": "healthcare",
                "request_type": "clinical_recommendation",
                "mentions_medication": True,
            },
            "confidence": 0.82,
        },
        "plugins": ["medical_safety_simplified"],
    }

    response = client.post("/evaluate/output", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["verdict"]["decision"] == "modify"
    assert body["verdict"]["risk_level"] == "high"
    assert body["evaluation_id"]


def test_plugins_endpoint():
    response = client.get("/plugins")
    assert response.status_code == 200
    plugins = response.json()["plugins"]
    plugin_ids = {p["plugin_id"] for p in plugins}
    assert "lgpd_br_simplified" in plugin_ids
    assert "medical_safety_simplified" in plugin_ids
    assert "internal_policy_simplified" in plugin_ids
