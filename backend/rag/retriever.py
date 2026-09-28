from __future__ import annotations

import re
from dataclasses import dataclass


# Demo MVP retrieval layer. This is keyword overlap matching, NOT semantic
# vector search. Replace later with FAISS/embeddings without changing callers
# of add_document / retrieve.


_TOKEN = re.compile(r"[a-z0-9]+")


@dataclass
class RetrievedChunk:
    source: str
    text: str
    score: float

    def as_dict(self) -> dict:
        return {"source": self.source, "text": self.text, "score": self.score}


class SimpleKeywordRetriever:
    def __init__(self) -> None:
        self._chunks: list[tuple[str, str]] = []

    def add_document(self, source: str, text: str) -> None:
        if not source or not str(source).strip():
            raise ValueError("Document source is required.")
        if text is None:
            raise ValueError("Document text is required.")
        self._chunks.append((str(source).strip(), str(text)))

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        scored = []
        for source, text in self._chunks:
            score = _keyword_score(query, text)
            scored.append(RetrievedChunk(source=source, text=text, score=score))
        scored.sort(key=lambda item: item.score, reverse=True)
        return [item.as_dict() for item in scored[: max(top_k, 0)]]


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall((text or "").lower())


def _keyword_score(query: str, text: str) -> float:
    query_tokens = _tokens(query)
    if not query_tokens:
        return 0.0
    doc_counts: dict[str, int] = {}
    for token in _tokens(text):
        doc_counts[token] = doc_counts.get(token, 0) + 1
    hits = sum(1 for token in query_tokens if doc_counts.get(token, 0) > 0)
    return hits / len(query_tokens)
