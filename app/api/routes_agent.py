from fastapi import APIRouter, Depends, HTTPException

from app.agent.models import AgentChatRequest, AgentChatResponse
from app.agent.orchestrator import AgentOrchestrationError, agent_orchestrator
from app.api.dependencies import require_api_key

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
def agent_chat(payload: AgentChatRequest, _: None = Depends(require_api_key)) -> AgentChatResponse:
    try:
        return agent_orchestrator.run(payload)
    except AgentOrchestrationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
