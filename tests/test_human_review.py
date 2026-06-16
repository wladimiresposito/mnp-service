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


def test_resolve_human_review_item():
    payload = {
        "tenant_id": "clinic-demo",
        "session_id": "review-test-001",
        "user_id": "user-review",
        "user_text": "Pode?",
        "mode": "heuristic",
        "low_confidence_threshold": 0.70,
        "enqueue_human_review_on_fallback": True
    }

    extraction = client.post("/extract/facts", json=payload)
    assert extraction.status_code == 200
    review_id = extraction.json()["review_id"]
    assert review_id

    resolution = client.post(
        f"/human-review/{review_id}/resolve",
        json={
            "resolution": {
                "approved_facts": {
                    "domain": "general",
                    "request_type": "unknown",
                    "fact_extraction_confidence": 0.95
                },
                "reviewer": "test"
            }
        }
    )

    assert resolution.status_code == 200
    assert resolution.json()["status"] == "resolved"

    fetched = client.get(f"/human-review/{review_id}")
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "resolved"
