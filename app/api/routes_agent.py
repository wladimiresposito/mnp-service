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
