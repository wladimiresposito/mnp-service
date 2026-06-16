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

from app.core.middleware import NormativeMiddleware
from app.core.models import Context, DraftAnswer
from app.plugins.lgpd_br_simplified.plugin import LgpdBrSimplifiedPlugin
from app.plugins.medical_safety_simplified.plugin import MedicalSafetySimplifiedPlugin


def test_health_medication_request_returns_modify():
    context = Context(
        tenant_id="clinic-demo",
        user_text="Tenho uma mancha na pele. Posso usar corticoide?",
        facts={
            "domain": "healthcare",
            "contains_sensitive_health_data": True,
            "request_type": "clinical_recommendation",
            "mentions_medication": True,
            "fact_extraction_confidence": 0.83,
        },
    )
    draft = DraftAnswer(
        text="Pode usar a pomada com corticoide. É seguro usar.",
        facts=context.facts,
    )

    mnp = NormativeMiddleware([LgpdBrSimplifiedPlugin(), MedicalSafetySimplifiedPlugin()])
    verdict = mnp.evaluate_all(context=context, draft=draft)

    assert verdict.decision == "modify"
    assert verdict.risk_level == "high"
    assert "unsafe_medical_advice_in_output" in verdict.violated_rules


def test_general_question_returns_allow():
    context = Context(
        tenant_id="clinic-demo",
        user_text="Qual o horário de funcionamento?",
        facts={
            "domain": "general",
            "request_type": "general_information",
            "fact_extraction_confidence": 0.95,
        },
    )
    draft = DraftAnswer(
        text="A clínica funciona de segunda a sexta.",
        facts=context.facts,
    )

    mnp = NormativeMiddleware([LgpdBrSimplifiedPlugin(), MedicalSafetySimplifiedPlugin()])
    verdict = mnp.evaluate_all(context=context, draft=draft)

    assert verdict.decision == "allow"
