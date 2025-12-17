"""Data models for chunking."""

from pydantic import BaseModel, Field
from typing import Optional, List


class Chunk(BaseModel):
    """Represents a code chunk with metadata."""

    text: str = Field(..., description="The actual code/text content")
    file_path: str = Field(..., description="Relative path from repo root")
    line_range: str = Field(..., description="start_line-end_line (e.g., '45-67')")
    symbol_name: Optional[str] = Field(None, description="Function or class name (for AST chunks)")
    symbol_type: Optional[str] = Field(None, description="'function' | 'class' | None")
    token_count: int = Field(0, description="Number of tokens in chunk")
    chunk_id: str = Field("", description="Unique identifier for ChromaDB")


class RetrievalResult(BaseModel):
    """Result from retrieval operation."""

    chunks: List[Chunk] = Field(..., description="List of retrieved chunks")
    max_similarity: float = Field(..., description="Maximum similarity score (1 - distance)")
    num_chunks_above_threshold: int = Field(..., description="Number of chunks above similarity threshold")
    distances: List[float] = Field(..., description="Distance scores for each chunk (lower is more similar)")
