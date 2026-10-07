from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeDocumentResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    source: str
    extension: str
    characters: int
    chunks_created: int
    status: str
    created_at: datetime
    updated_at: datetime


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=20)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)


class KnowledgeSearchResult(BaseModel):
    source: str
    text: str
    score: float
    chunk_id: int | str | None = None


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeSearchResult]


class KnowledgeStatsResponse(BaseModel):
    documents: int
    chunks: int
