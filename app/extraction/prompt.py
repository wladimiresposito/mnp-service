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

from app.extraction.models import NormativeFacts


SYSTEM_PROMPT = """You are a normative fact extractor for a Pluggable Normative Middleware.

Extract only facts that are relevant for normative evaluation.
Do not decide whether the system should allow, modify, block, or escalate.
Do not give advice.
Do not rewrite the answer.
Return only valid JSON matching the provided schema.
If uncertain, set fact_extraction_confidence below 0.70 and explain uncertainty_reasons.
"""


def build_user_prompt(user_text: str) -> str:
    schema = NormativeFacts.model_json_schema()
    return (
        "Extract normative facts from the following user message.\n\n"
        "JSON Schema:\n"
        f"{schema}\n\n"
        "User message:\n"
        f"{user_text}\n\n"
        "Return only JSON."
    )
