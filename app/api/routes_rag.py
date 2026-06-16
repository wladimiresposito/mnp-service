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

from fastapi import APIRouter, Depends

from app.api.dependencies import require_api_key
from app.rag.models import RAGSearchRequest, RAGSearchResponse
from app.rag.retriever import get_retriever

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/search", response_model=RAGSearchResponse)
def rag_search(payload: RAGSearchRequest, _: None = Depends(require_api_key)) -> RAGSearchResponse:
    results = get_retriever().search(payload.query, top_k=payload.top_k)
    return RAGSearchResponse(
        query=payload.query,
        tenant_id=payload.tenant_id,
        results=results,
    )
