from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None


class SourceItem(BaseModel):
    chunk_id: str
    source_id: str
    tool_type: str
    title: str
    url: str


class QueryResponse(BaseModel):
    answer_id: str
    query_text: str
    answer_text: str
    result_status: str
    confidence_score: float
    confidence_factors: Dict[str, Any]
    sources: List[SourceItem]
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int


class FeedbackRequest(BaseModel):
    answer_id: str
    rating: int
    helpful: bool
    comment: Optional[str] = None
    user_id: Optional[str] = None


class IngestResponse(BaseModel):
    status: str
    sources_ingested: int
    chunks_ingested: int
