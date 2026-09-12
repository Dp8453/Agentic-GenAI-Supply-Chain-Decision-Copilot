from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class RAGMetadataFilter(BaseModel):
    supplier: Optional[str] = None
    document_type: Optional[str] = None
    section: Optional[str] = None


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="Natural language search query")
    top_k: int = Field(5, gt=0, le=20, description="Maximum relevant chunks to return (1 to 20)")
    similarity_threshold: float = Field(0.35, ge=0.0, le=1.0, description="Minimum cosine similarity score")
    filters: Optional[RAGMetadataFilter] = None


class RAGChunkResult(BaseModel):
    chunk_id: int
    document_name: str
    document_type: str
    chunk_index: int
    content: str
    similarity: float
    metadata: Dict[str, Any]


class RAGQueryResponse(BaseModel):
    query: str
    top_k: int
    total_retrieved: int
    results: List[RAGChunkResult]
