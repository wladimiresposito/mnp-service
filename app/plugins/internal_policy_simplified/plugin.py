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

from app.core.models import ActionPlan, Decision, PluginMetadata, RiskLevel, ToolCall, Verdict
from app.core.module import NormativeModule


class InternalPolicySimplifiedPlugin(NormativeModule):
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            plugin_id="internal_policy_simplified",
            plugin_version="2026.1-demo",
            jurisdiction="internal",
            domain="company_policy",
            source="MNP MVP internal safety policy",
            updated_at="2026-06-12",
            binding=False,
        )

    def evaluate_plan(self, plan: ActionPlan) -> Verdict:
        meta = self.metadata()
        side_effect_actions = [
            action for action in plan.actions
            if action.get("side_effect") is True
        ]

        if side_effect_actions and plan.confidence < 0.75:
            return Verdict(
                decision=Decision.ESCALATE,
                risk_level=RiskLevel.HIGH,
                violated_rules=["low_confidence_plan_with_side_effect"],
                required_changes=["request_human_review_before_execution"],
                explanation="O plano possui ação com efeito externo e confiança baixa.",
                trace=[{"side_effect_actions": side_effect_actions, "confidence": plan.confidence}],
                plugin_id=meta.plugin_id,
                plugin_version=meta.plugin_version,
            )

        return Verdict.allow(meta.plugin_id, meta.plugin_version, "Plano compatível com política interna simplificada.")

    def evaluate_tool_call(self, tool_call: ToolCall) -> Verdict:
        meta = self.metadata()

        if tool_call.requires_side_effect:
            return Verdict(
                decision=Decision.MODIFY,
                risk_level=RiskLevel.MEDIUM,
                violated_rules=["external_side_effect_requires_audit"],
                required_changes=[
                    "ensure_tool_call_logged",
                    "ensure_user_or_operator_authorization_when_needed",
                ],
                explanation="Toda chamada com efeito externo deve ser auditada e autorizável.",
                plugin_id=meta.plugin_id,
                plugin_version=meta.plugin_version,
            )

        return Verdict.allow(meta.plugin_id, meta.plugin_version, "Tool call sem efeito externo relevante.")
