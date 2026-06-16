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

from __future__ import annotations

import json
import urllib.request


BASE_URL = "http://localhost:8000"


def get(path: str) -> dict:
    with urllib.request.urlopen(BASE_URL + path, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def post(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    print("health:", get("/health")["status"])
    print("ready:", get("/system/ready")["status"])
    print("plugins:", len(get("/plugins")["plugins"]))
    print("tenants:", len(get("/tenants")["tenants"]))

    payload = {
        "tenant_id": "clinic-demo",
        "session_id": "smoke-001",
        "user_id": "smoke-user",
        "user_text": "Tenho uma mancha na pele. Posso usar corticoide?",
        "extract_mode": "heuristic",
        "top_k": 3,
    }
    result = post("/agent/chat", payload)
    print("agent action:", result["action_taken"])
    print("verdict:", result["verdict"]["decision"])
    print("evaluation:", result["evaluation_id"])


if __name__ == "__main__":
    main()
