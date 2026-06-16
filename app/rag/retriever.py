from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from app.config.settings import settings
from app.rag.models import RAGDocument, RAGSearchResult


STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "da", "do", "das", "dos", "e",
    "em", "para", "por", "com", "sem", "que", "se", "ao", "à", "no", "na",
    "nos", "nas", "the", "is", "are", "to", "of", "and",
}


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9_]+", text.lower())
    return [t for t in tokens if len(t) > 2 and t not in STOPWORDS]


class SimpleRAGRetriever:
    """
    Very small deterministic RAG retriever for MVP v0.6.

    It loads .md/.txt files from app/rag/knowledge_base and scores documents
    using lexical overlap. It is intentionally replaceable by pgvector/RRF later.
    """

    def __init__(self, knowledge_base_path: str) -> None:
        self.knowledge_base_path = Path(knowledge_base_path)
        self.documents = self._load_documents()

    def search(self, query: str, top_k: int | None = None) -> list[RAGSearchResult]:
        top_k = top_k or settings.rag_top_k
        query_terms = set(tokenize(query))

        scored: list[tuple[float, RAGDocument]] = []
        for doc in self.documents:
            doc_terms = tokenize(doc.title + " " + doc.text)
            doc_term_set = set(doc_terms)

            if not doc_terms:
                continue

            overlap = query_terms & doc_term_set
            score = len(overlap) / max(len(query_terms), 1)

            # small boost for exact medication/health policy terms
            lower_doc = doc.text.lower()
            for term in query_terms:
                if term in lower_doc:
                    score += 0.03

            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda item: item[0], reverse=True)

        return [
            RAGSearchResult(
                doc_id=doc.doc_id,
                title=doc.title,
                source=doc.source,
                snippet=self._snippet(doc.text, query_terms),
                score=round(score, 4),
            )
            for score, doc in scored[:top_k]
        ]

    def _load_documents(self) -> list[RAGDocument]:
        if not self.knowledge_base_path.exists():
            return []

        docs: list[RAGDocument] = []
        for idx, path in enumerate(sorted(self.knowledge_base_path.glob("*"))):
            if path.suffix.lower() not in {".md", ".txt"}:
                continue
            text = path.read_text(encoding="utf-8")
            title = self._extract_title(text) or path.stem.replace("_", " ").title()
            docs.append(
                RAGDocument(
                    doc_id=path.stem,
                    title=title,
                    source=str(path),
                    text=text,
                )
            )
        return docs

    def _extract_title(self, text: str) -> str | None:
        for line in text.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return None

    def _snippet(self, text: str, query_terms: set[str]) -> str:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            return text[:400]

        best = max(
            paragraphs,
            key=lambda p: len(set(tokenize(p)) & query_terms),
        )
        return best[:600]


@lru_cache(maxsize=1)
def get_retriever() -> SimpleRAGRetriever:
    return SimpleRAGRetriever(settings.rag_knowledge_base_path)
