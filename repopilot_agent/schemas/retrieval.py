from __future__ import annotations

from pydantic import BaseModel, Field


class CodeChunk(BaseModel):
    chunk_id: str = Field(description="Stable chunk id.")
    file_path: str = Field(description="Repository-relative file path.")
    start_line: int = Field(description="1-based start line.")
    end_line: int = Field(description="1-based end line.")
    content: str = Field(description="Chunk text.")
    symbols: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class RetrievedChunk(CodeChunk):
    score: float = Field(description="Retrieval score.")
    reasons: list[str] = Field(default_factory=list)


class RetrievalResult(BaseModel):
    queries: list[str]
    retrieved_chunks: list[RetrievedChunk]
    retrieved_files: list[str]
    context: str
    summary: str