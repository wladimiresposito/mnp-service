from __future__ import annotations

from app.agent.generator import MockAgentGenerator, deterministic_safe_rewrite
from app.agent.models import AgentChatRequest, AgentChatResponse, AgentStep
from app.audit.factory import get_audit_repository
from app.core.middleware import NormativeMiddleware
from app.core.models import Context, Decision, Phase
from app.core.registry import PluginResolutionError, default_registry
from app.extraction.models import FactExtractionRequest
from app.extraction.service import extract_and_validate
from app.rag.retriever import get_retriever


class AgentOrchestrationError(RuntimeError):
    pass


class AgentOrchestrator:
    def __init__(self) -> None:
        self.generator = MockAgentGenerator()

    def run(self, payload: AgentChatRequest) -> AgentChatResponse:
        steps: list[AgentStep] = []

        extraction = extract_and_validate(
            FactExtractionRequest(
                tenant_id=payload.tenant_id,
                session_id=payload.session_id,
                user_id=payload.user_id,
                user_text=payload.user_text,
                mode=payload.extract_mode,
                enqueue_human_review_on_fallback=payload.enqueue_human_review_on_fallback,
            )
        )
        steps.append(
            AgentStep(
                name="fact_extraction",
                status="ok" if extraction.valid else "invalid",
                detail={
                    "mode": extraction.mode,
                    "confidence": extraction.confidence,
                    "requires_human_review": extraction.requires_human_review,
                    "review_id": extraction.review_id,
                },
            )
        )

        facts = extraction.facts

        # If extraction itself is too uncertain, escalate before generation.
        if extraction.requires_human_review:
            context = Context(
                tenant_id=payload.tenant_id,
                session_id=payload.session_id,
                user_id=payload.user_id,
                user_text=payload.user_text,
                facts=facts.model_dump(mode="json"),
            )

            plugins, cfg, active_ids = default_registry.resolve_for_tenant(payload.tenant_id, payload.plugins)
            mnp = NormativeMiddleware(plugins, composition=cfg.composition)
            verdict = mnp.evaluate_input(context)

            evaluation_id = get_audit_repository().save_evaluation(
                tenant_id=payload.tenant_id,
                session_id=payload.session_id,
                user_id=payload.user_id,
                phase=Phase.ALL,
                request_payload={
                    "agent_request": payload.model_dump(mode="json"),
                    "extraction": extraction.model_dump(mode="json"),
                    "short_circuit": "human_review_required",
                },
                verdict=verdict,
                active_plugins=active_ids,
                tenant_config=cfg.model_dump(mode="json"),
            )

            return AgentChatResponse(
                tenant_id=payload.tenant_id,
                session_id=payload.session_id,
                user_id=payload.user_id,
                user_text=payload.user_text,
                extraction=extraction,
                retrieved_context=[],
                plan=self.generator.build_plan(payload.user_text, facts, []),
                tool_call=None,
                draft=self.generator.build_draft(payload.user_text, facts, []),
                verdict=verdict,
                final_answer="Preciso encaminhar esta solicitação para revisão humana antes de responder com segurança.",
                action_taken="escalated",
                evaluation_id=evaluation_id,
                review_id=extraction.review_id,
                active_plugins=active_ids,
                steps=steps + [AgentStep(name="short_circuit", status="escalated", detail={"reason": extraction.fallback_reason})],
            )

        retrieved = get_retriever().search(payload.user_text, top_k=payload.top_k)
        steps.append(
            AgentStep(
                name="rag_search",
                status="ok",
                detail={"results": len(retrieved)},
            )
        )

        plan = self.generator.build_plan(payload.user_text, facts, retrieved)
        tool_call = self.generator.maybe_tool_call(payload.user_text, facts, payload.allow_tool_calls)
        draft = self.generator.build_draft(payload.user_text, facts, retrieved)

        context = Context(
            tenant_id=payload.tenant_id,
            session_id=payload.session_id,
            user_id=payload.user_id,
            user_text=payload.user_text,
            facts=facts.model_dump(mode="json"),
        )

        try:
            plugins, cfg, active_ids = default_registry.resolve_for_tenant(payload.tenant_id, payload.plugins)
        except PluginResolutionError as exc:
            raise AgentOrchestrationError(str(exc)) from exc

        mnp = NormativeMiddleware(plugins, composition=cfg.composition)
        verdict = mnp.evaluate_all(
            context=context,
            plan=plan,
            tool_call=tool_call,
            draft=draft,
        )
        steps.append(
            AgentStep(
                name="mnp_evaluate",
                status=verdict.decision.value,
                detail={
                    "risk_level": verdict.risk_level.value,
                    "violated_rules": verdict.violated_rules,
                    "required_changes": verdict.required_changes,
                },
            )
        )

        evaluation_id = get_audit_repository().save_evaluation(
            tenant_id=payload.tenant_id,
            session_id=payload.session_id,
            user_id=payload.user_id,
            phase=Phase.ALL,
            request_payload={
                "agent_request": payload.model_dump(mode="json"),
                "extraction": extraction.model_dump(mode="json"),
                "retrieved_context": [r.model_dump(mode="json") for r in retrieved],
                "plan": plan.model_dump(mode="json"),
                "tool_call": tool_call.model_dump(mode="json") if tool_call else None,
                "draft": draft.model_dump(mode="json"),
            },
            verdict=verdict,
            active_plugins=active_ids,
            tenant_config=cfg.model_dump(mode="json"),
        )

        if verdict.decision == Decision.ALLOW:
            final_answer = draft.text
            action_taken = "answered"
        elif verdict.decision == Decision.MODIFY:
            final_answer = deterministic_safe_rewrite(
                payload.user_text,
                facts,
                retrieved,
                verdict.required_changes,
            )
            action_taken = "modified"
        elif verdict.decision == Decision.ESCALATE:
            final_answer = (
                "Este caso precisa de revisão humana antes de uma resposta final. "
                "Vou encaminhar com os fatos e a justificativa normativa registrada."
            )
            action_taken = "escalated"
        else:
            final_answer = "Não posso executar ou responder essa solicitação conforme as políticas normativas ativas."
            action_taken = "blocked"

        steps.append(
            AgentStep(
                name="finalize",
                status=action_taken,
                detail={"evaluation_id": evaluation_id},
            )
        )

        return AgentChatResponse(
            tenant_id=payload.tenant_id,
            session_id=payload.session_id,
            user_id=payload.user_id,
            user_text=payload.user_text,
            extraction=extraction,
            retrieved_context=retrieved,
            plan=plan,
            tool_call=tool_call,
            draft=draft,
            verdict=verdict,
            final_answer=final_answer,
            action_taken=action_taken,
            evaluation_id=evaluation_id,
            review_id=extraction.review_id,
            active_plugins=active_ids,
            steps=steps,
        )


agent_orchestrator = AgentOrchestrator()
