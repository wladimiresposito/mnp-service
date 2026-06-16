from __future__ import annotations

from pydantic import BaseModel, Field


class RAGSearchRequest(BaseModel):
    query: str
    tenant_id: str = "default"
    top_k: int | None = None


class RAGDocument(BaseModel):
    doc_id: str
    title: str
    source: str
    text: str


class RAGSearchResult(BaseModel):
    doc_id: str
    title: str
    source: str
    snippet: str
    score: float


class RAGSearchResponse(BaseModel):
    query: str
    tenant_id: str
    results: list[RAGSearchResult] = Field(default_factory=list)
