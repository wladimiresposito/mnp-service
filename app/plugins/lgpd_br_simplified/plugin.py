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

from app.core.models import Context, Decision, DraftAnswer, PluginMetadata, RiskLevel, ToolCall, Verdict
from app.core.module import NormativeModule


class LgpdBrSimplifiedPlugin(NormativeModule):
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            plugin_id="lgpd_br_simplified",
            plugin_version="2026.1-demo",
            jurisdiction="BR",
            domain="data_protection",
            source="LGPD simplified demo rules",
            updated_at="2026-06-12",
        )

    def evaluate_input(self, context: Context) -> Verdict:
        meta = self.metadata()
        facts = context.facts
        confidence = float(facts.get("fact_extraction_confidence", 1.0))

        if facts.get("contains_sensitive_health_data") and confidence < 0.70:
            return Verdict(
                decision=Decision.ESCALATE,
                risk_level=RiskLevel.HIGH,
                violated_rules=["uncertain_sensitive_data_classification"],
                required_changes=["request_human_review_or_reclassify"],
                explanation="A entrada parece conter dado sensível, mas a confiança da extração é baixa.",
                plugin_id=meta.plugin_id,
                plugin_version=meta.plugin_version,
            )

        if facts.get("contains_sensitive_health_data") and not facts.get("legal_basis_confirmed", False):
            return Verdict(
                decision=Decision.MODIFY,
                risk_level=RiskLevel.HIGH,
                violated_rules=["sensitive_health_data_requires_valid_legal_basis"],
                required_changes=[
                    "confirm_legal_basis",
                    "confirm_purpose",
                    "avoid_unnecessary_sensitive_data_collection",
                    "log_sensitive_data_flag",
                ],
                explanation="A interação envolve dado sensível de saúde e deve confirmar base legal/finalidade antes de tratamento adicional.",
                trace=[{"fact": "contains_sensitive_health_data", "value": True}],
                plugin_id=meta.plugin_id,
                plugin_version=meta.plugin_version,
            )

        return Verdict.allow(meta.plugin_id, meta.plugin_version, "Nenhum impedimento LGPD simplificado identificado.")

    def evaluate_tool_call(self, tool_call: ToolCall) -> Verdict:
        meta = self.metadata()
        facts = tool_call.facts

        if tool_call.requires_side_effect and facts.get("contains_sensitive_health_data"):
            return Verdict(
                decision=Decision.MODIFY,
                risk_level=RiskLevel.HIGH,
                violated_rules=["external_action_with_sensitive_data_requires_controls"],
                required_changes=[
                    "log_sensitive_data_flag",
                    "confirm_purpose",
                    "confirm_recipient_authorization",
                ],
                explanation="A chamada de ferramenta tem efeito externo e envolve dado sensível.",
                plugin_id=meta.plugin_id,
                plugin_version=meta.plugin_version,
            )

        if facts.get("reveals_third_party_personal_data"):
            return Verdict(
                decision=Decision.BLOCK,
                risk_level=RiskLevel.CRITICAL,
                violated_rules=["unauthorized_third_party_personal_data_disclosure"],
                required_changes=["block_disclosure"],
                explanation="A ação revela dado pessoal de terceiro sem autorização explícita.",
                plugin_id=meta.plugin_id,
                plugin_version=meta.plugin_version,
            )

        return Verdict.allow(meta.plugin_id, meta.plugin_version, "Tool call compatível com regras LGPD simplificadas.")

    def evaluate_output(self, draft: DraftAnswer) -> Verdict:
        meta = self.metadata()
        text = draft.text.lower()

        if draft.facts.get("contains_sensitive_health_data") and "diagnóstico definitivo" in text:
            return Verdict(
                decision=Decision.MODIFY,
                risk_level=RiskLevel.HIGH,
                violated_rules=["avoid_overconfident_sensitive_health_inference"],
                required_changes=["remove_definitive_diagnostic_claim"],
                explanation="A resposta faz inferência sensível de saúde de forma conclusiva demais.",
                plugin_id=meta.plugin_id,
                plugin_version=meta.plugin_version,
            )

        return Verdict.allow(meta.plugin_id, meta.plugin_version, "Saída compatível com regras LGPD simplificadas.")
