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
from app.extraction.heuristic_extractor import extract_normative_facts
from app.plugins.lgpd_br_simplified.plugin import LgpdBrSimplifiedPlugin
from app.plugins.medical_safety_simplified.plugin import MedicalSafetySimplifiedPlugin


def main() -> None:
    user_text = "Estou com uma mancha na pele. Tenho corticoide em casa. Posso usar?"
    facts = extract_normative_facts(user_text)

    context = Context(
        tenant_id="clinic-demo",
        user_id="user-123",
        session_id="sess-demo",
        user_text=user_text,
        facts=facts,
    )

    draft = DraftAnswer(
        text="Pode usar a pomada com corticoide por alguns dias. É seguro usar.",
        facts=facts,
    )

    mnp = NormativeMiddleware([
        LgpdBrSimplifiedPlugin(),
        MedicalSafetySimplifiedPlugin(),
    ])

    verdict = mnp.evaluate_all(context=context, draft=draft)
    print(verdict.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
