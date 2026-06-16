from __future__ import annotations

from app.asp.engine import temporal_consent_engine
from app.asp.models import TemporalAspInput, TemporalEvent
from app.core.models import Context, Decision, PluginMetadata, RiskLevel, Verdict
from app.core.module import NormativeModule


class LgpdTemporalAspPlugin(NormativeModule):
    """
    Experimental ASP/Clingo plugin for temporal consent.

    It evaluates whether active consent holds at current_time for a purpose.
    If clingo is not installed, it uses a Python fallback with equivalent
    grant/revoke latest-event semantics.
    """

    DEFAULT_PURPOSE = "process_health_data_for_pre_anamnesis"

    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            plugin_id="lgpd_temporal_asp",
            plugin_version="2026.1-experimental",
            jurisdiction="BR",
            domain="data_protection_temporal",
            source="Experimental ASP/Event Calculus-style consent rules",
            updated_at="2026-06-12",
        )

    def evaluate_input(self, context: Context) -> Verdict:
        meta = self.metadata()
        facts = context.facts

        if not facts.get("contains_sensitive_health_data", False):
            return Verdict.allow(
                meta.plugin_id,
                meta.plugin_version,
                "Sem dado sensível de saúde para avaliação temporal de consentimento.",
            )

        subject = context.user_id or facts.get("subject") or "anonymous"
        purpose = facts.get("purpose") or self.DEFAULT_PURPOSE
        current_time = int(facts.get("current_time", 100))

        events = [
            TemporalEvent.model_validate(event)
            for event in facts.get("temporal_events", [])
        ]

        result = temporal_consent_engine.evaluate(
            TemporalAspInput(
                subject=subject,
                purpose=purpose,
                current_time=current_time,
                sensitive_health_data=True,
                events=events,
            )
        )

        if result.forbidden:
            return Verdict(
                decision=Decision.MODIFY,
                risk_level=RiskLevel.HIGH,
                violated_rules=[
                    "temporal_sensitive_health_processing_without_active_consent"
                ],
                required_changes=result.required_changes,
                explanation=(
                    "O plugin ASP temporal não encontrou consentimento ativo "
                    "para a finalidade no instante avaliado."
                ),
                trace=[
                    {
                        "asp_result": result.model_dump(mode="json"),
                        "subject": subject,
                        "purpose": purpose,
                        "current_time": current_time,
                    }
                ],
                plugin_id=meta.plugin_id,
                plugin_version=meta.plugin_version,
            )

        return Verdict(
            decision=Decision.ALLOW,
            risk_level=RiskLevel.LOW,
            explanation=(
                "Consentimento temporal ativo encontrado para a finalidade avaliada."
            ),
            trace=[
                {
                    "asp_result": result.model_dump(mode="json"),
                    "subject": subject,
                    "purpose": purpose,
                    "current_time": current_time,
                }
            ],
            plugin_id=meta.plugin_id,
            plugin_version=meta.plugin_version,
        )
