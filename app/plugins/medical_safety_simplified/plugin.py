from __future__ import annotations

from app.core.models import Context, Decision, DraftAnswer, PluginMetadata, RiskLevel, Verdict
from app.core.module import NormativeModule


class MedicalSafetySimplifiedPlugin(NormativeModule):
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            plugin_id="medical_safety_simplified",
            plugin_version="2026.1-demo",
            jurisdiction="BR",
            domain="healthcare",
            source="Generic clinical safety policy demo",
            updated_at="2026-06-12",
        )

    def evaluate_input(self, context: Context) -> Verdict:
        meta = self.metadata()
        facts = context.facts

        if facts.get("has_urgent_symptoms"):
            return Verdict(
                decision=Decision.ESCALATE,
                risk_level=RiskLevel.CRITICAL,
                violated_rules=["urgent_symptoms_require_human_or_emergency_guidance"],
                required_changes=[
                    "do_not_handle_as_routine_chat",
                    "advise_urgent_professional_evaluation",
                    "escalate_to_human_review",
                ],
                explanation="A entrada sugere possível urgência e deve ser escalada.",
                plugin_id=meta.plugin_id,
                plugin_version=meta.plugin_version,
            )

        if facts.get("request_type") == "clinical_recommendation" and facts.get("mentions_medication"):
            return Verdict(
                decision=Decision.MODIFY,
                risk_level=RiskLevel.HIGH,
                violated_rules=["clinical_recommendation_with_medication_requires_professional_evaluation"],
                required_changes=[
                    "do_not_recommend_medication_use",
                    "advise_professional_evaluation",
                    "offer_appointment_or_human_review",
                ],
                explanation="A solicitação envolve sintoma e possível uso de medicamento. O sistema não deve recomendar uso individualizado.",
                trace=[
                    {"fact": "request_type", "value": facts.get("request_type")},
                    {"fact": "mentions_medication", "value": facts.get("mentions_medication")},
                ],
                plugin_id=meta.plugin_id,
                plugin_version=meta.plugin_version,
            )

        if facts.get("request_type") == "clinical_recommendation":
            return Verdict(
                decision=Decision.MODIFY,
                risk_level=RiskLevel.MEDIUM,
                violated_rules=["clinical_recommendation_requires_careful_general_guidance"],
                required_changes=[
                    "avoid_diagnosis",
                    "provide_general_information_only",
                    "advise_professional_evaluation_when_needed",
                ],
                explanation="A solicitação parece pedir orientação clínica individualizada.",
                plugin_id=meta.plugin_id,
                plugin_version=meta.plugin_version,
            )

        return Verdict.allow(meta.plugin_id, meta.plugin_version, "Entrada sem risco clínico relevante detectado.")

    def evaluate_output(self, draft: DraftAnswer) -> Verdict:
        meta = self.metadata()
        text = draft.text.lower()
        unsafe_phrases = [
            "pode usar a pomada",
            "use a pomada",
            "recomendo usar",
            "não precisa consultar",
            "é seguro usar",
            "não há risco",
        ]

        matched = [phrase for phrase in unsafe_phrases if phrase in text]

        if draft.facts.get("domain") == "healthcare" and matched:
            return Verdict(
                decision=Decision.MODIFY,
                risk_level=RiskLevel.HIGH,
                violated_rules=["unsafe_medical_advice_in_output"],
                required_changes=[
                    "remove_direct_medication_recommendation",
                    "include_safety_disclaimer",
                    "advise_professional_evaluation",
                    "offer_appointment_or_human_review",
                ],
                explanation="O rascunho contém orientação clínica individualizada potencialmente insegura.",
                trace=[{"matched_unsafe_phrases": matched}],
                plugin_id=meta.plugin_id,
                plugin_version=meta.plugin_version,
            )

        return Verdict.allow(meta.plugin_id, meta.plugin_version, "Saída sem aconselhamento clínico individualizado detectado.")
