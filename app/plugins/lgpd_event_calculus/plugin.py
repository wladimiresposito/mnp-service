from __future__ import annotations

from app.core.models import Context, Decision, PluginMetadata, RiskLevel, Verdict
from app.core.module import NormativeModule
from app.event_calculus.engine import event_calculus_engine
from app.event_calculus.models import ECEvent, ECScenario


class LgpdEventCalculusPlugin(NormativeModule):
    """
    Explicit Event Calculus plugin.

    Compared to lgpd_temporal_asp, this plugin exposes a richer temporal model:
    - fluents
    - clipping
    - purpose confirmation
    - processing state
    - obligations
    - exceptions
    - consequences
    """

    DEFAULT_PURPOSE = "process_health_data_for_pre_anamnesis"

    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            plugin_id="lgpd_event_calculus",
            plugin_version="2026.1-experimental",
            jurisdiction="BR",
            domain="data_protection_event_calculus",
            source="Explicit Event Calculus-style LGPD temporal demo rules",
            updated_at="2026-06-12",
        )

    def evaluate_input(self, context: Context) -> Verdict:
        meta = self.metadata()
        facts = context.facts

        if not facts.get("contains_sensitive_health_data", False):
            return Verdict.allow(
                meta.plugin_id,
                meta.plugin_version,
                "Sem dado sensível de saúde para avaliação Event Calculus.",
            )

        subject = context.user_id or facts.get("subject") or "anonymous"
        purpose = facts.get("purpose") or self.DEFAULT_PURPOSE

        events = [
            ECEvent.model_validate(event)
            for event in facts.get("ec_events", facts.get("temporal_events", []))
        ]

        scenario = ECScenario(
            subject=subject,
            purpose=purpose,
            current_time=int(facts.get("current_time", 100)),
            data_category=facts.get("data_category", "health"),
            processing_action=facts.get("processing_action", "process_health_data"),
            events=events,
            requires_legal_basis=bool(facts.get("requires_legal_basis", True)),
            requires_purpose_confirmation=bool(facts.get("requires_purpose_confirmation", True)),
            emergency_exception=bool(facts.get("emergency_exception", False)),
            human_review_override=bool(facts.get("human_review_override", False)),
        )

        result = event_calculus_engine.evaluate(scenario)

        if result.decision.forbidden:
            decision = Decision.ESCALATE if result.decision.requires_escalation else Decision.MODIFY
            return Verdict(
                decision=decision,
                risk_level=RiskLevel(result.decision.risk_level),
                violated_rules=result.decision.violated_rules,
                required_changes=result.decision.required_changes,
                explanation=(
                    "O plugin Event Calculus identificou violação temporal/normativa "
                    "envolvendo dado sensível, finalidade ou consentimento."
                ),
                trace=[
                    {
                        "event_calculus_result": result.model_dump(mode="json"),
                        "subject": subject,
                        "purpose": purpose,
                    }
                ],
                plugin_id=meta.plugin_id,
                plugin_version=meta.plugin_version,
            )

        # Breach consequence can require escalation even if processing is not forbidden.
        if result.decision.requires_escalation:
            return Verdict(
                decision=Decision.ESCALATE,
                risk_level=RiskLevel(result.decision.risk_level),
                violated_rules=result.decision.violated_rules,
                required_changes=result.decision.required_changes,
                explanation="O plugin Event Calculus encontrou consequência que exige escalonamento.",
                trace=[
                    {
                        "event_calculus_result": result.model_dump(mode="json"),
                        "subject": subject,
                        "purpose": purpose,
                    }
                ],
                plugin_id=meta.plugin_id,
                plugin_version=meta.plugin_version,
            )

        return Verdict(
            decision=Decision.ALLOW,
            risk_level=RiskLevel.LOW,
            explanation="Event Calculus não encontrou impedimento temporal para a ação avaliada.",
            trace=[
                {
                    "event_calculus_result": result.model_dump(mode="json"),
                    "subject": subject,
                    "purpose": purpose,
                }
            ],
            plugin_id=meta.plugin_id,
            plugin_version=meta.plugin_version,
        )
