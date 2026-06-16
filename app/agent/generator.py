from __future__ import annotations

from app.core.models import ActionPlan, DraftAnswer, ToolCall
from app.extraction.models import NormativeFacts
from app.rag.models import RAGSearchResult


class MockAgentGenerator:
    """
    Deterministic generator for MVP v0.6.

    It intentionally may generate a risky draft for clinical medication questions,
    so the MNP can demonstrate modify/escalate behavior.
    """

    def build_plan(
        self,
        user_text: str,
        facts: NormativeFacts,
        retrieved_context: list[RAGSearchResult],
    ) -> ActionPlan:
        actions = [
            {
                "type": "retrieve_context",
                "target": "local_knowledge_base",
                "side_effect": False,
            },
            {
                "type": "generate_answer",
                "target": "user",
                "side_effect": False,
            },
        ]

        if facts.external_communication:
            actions.append(
                {
                    "type": "send_external_message",
                    "target": "external_channel",
                    "side_effect": True,
                }
            )

        return ActionPlan(
            goal="answer_user_with_normative_control",
            actions=actions,
            facts=facts.model_dump(mode="json"),
            confidence=max(facts.fact_extraction_confidence, 0.1),
        )

    def maybe_tool_call(self, user_text: str, facts: NormativeFacts, allow_tool_calls: bool) -> ToolCall | None:
        if not allow_tool_calls:
            return None

        lower = user_text.lower()
        if "agendar" in lower or "marcar consulta" in lower:
            return ToolCall(
                name="create_appointment_request",
                arguments={
                    "channel": "internal_queue",
                    "summary": user_text[:300],
                },
                facts={
                    **facts.model_dump(mode="json"),
                    "external_communication": False,
                },
                requires_side_effect=True,
            )

        return None

    def build_draft(
        self,
        user_text: str,
        facts: NormativeFacts,
        retrieved_context: list[RAGSearchResult],
    ) -> DraftAnswer:
        text = self._draft_text(user_text, facts, retrieved_context)
        return DraftAnswer(
            text=text,
            facts=facts.model_dump(mode="json"),
            confidence=max(facts.fact_extraction_confidence, 0.1),
        )

    def _draft_text(
        self,
        user_text: str,
        facts: NormativeFacts,
        retrieved_context: list[RAGSearchResult],
    ) -> str:
        if facts.domain == "healthcare" and facts.mentions_medication:
            return (
                "Pode usar a pomada com corticoide por alguns dias. "
                "É seguro usar, e normalmente melhora a coceira."
            )

        if facts.domain == "healthcare" and facts.has_urgent_symptoms:
            return (
                "Pelo que você descreveu, pode ser algo que exige atenção. "
                "Vou encaminhar para avaliação humana."
            )

        if "horário" in user_text.lower() or "funcionamento" in user_text.lower():
            return (
                "A clínica atende de segunda a sexta-feira, das 8h às 18h, "
                "e aos sábados mediante agendamento."
            )

        if retrieved_context:
            return (
                "Com base nas informações disponíveis, posso ajudar de forma geral. "
                + retrieved_context[0].snippet[:350]
            )

        return "Posso ajudar com informações gerais e, se necessário, encaminhar para atendimento humano."


def deterministic_safe_rewrite(
    user_text: str,
    facts: NormativeFacts,
    retrieved_context: list[RAGSearchResult],
    required_changes: list[str],
) -> str:
    if facts.domain == "healthcare" and facts.has_urgent_symptoms:
        return (
            "Pelos sinais relatados, o mais seguro é procurar atendimento profissional com urgência. "
            "Não consigo avaliar ou descartar gravidade por chat. "
            "Vou sinalizar este caso para revisão humana."
        )

    if facts.domain == "healthcare" and facts.mentions_medication:
        return (
            "Não consigo avaliar essa situação nem indicar uso de corticoide sem uma avaliação profissional. "
            "Manchas na pele com coceira podem ter várias causas, e o uso inadequado de medicamento pode piorar o quadro "
            "ou mascarar sinais importantes. O mais seguro é agendar uma avaliação com um profissional de saúde. "
            "Se houver dor intensa, sangramento, crescimento rápido, febre ou piora importante, procure atendimento com urgência."
        )

    if "remove_direct_medication_recommendation" in required_changes:
        return (
            "Não posso recomendar uso individualizado de medicamento por chat. "
            "Posso fornecer informação geral e orientar avaliação profissional."
        )

    return (
        "Vou ajustar a resposta para respeitar as políticas normativas aplicáveis: "
        "posso dar informação geral, evitar afirmações conclusivas e encaminhar para atendimento humano quando necessário."
    )
