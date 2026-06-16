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
