"""
FastAPI application for ContextPM.
Start: uvicorn contextpm.api.app:app --reload --port 8000
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from contextpm.api.models import (
    FeedbackRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    SourceItem,
)
from contextpm.db.schema import init_db
from contextpm.ingestion.pipeline import run_ingestion
from contextpm.query.pipeline import run_query, submit_feedback

app = FastAPI(title="ContextPM API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
def ingest():
    """Re-runs the full ingestion pipeline from synthetic data files."""
    stats = run_ingestion()
    return IngestResponse(
        status="completed",
        sources_ingested=stats["sources"],
        chunks_ingested=stats["chunks"],
    )


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")
    result = run_query(req.query, user_id=req.user_id)
    return QueryResponse(
        answer_id=result["answer_id"],
        query_text=result["query_text"],
        answer_text=result["answer_text"],
        result_status=result["result_status"],
        confidence_score=result["confidence_score"],
        confidence_factors=result["confidence_factors"],
        sources=[SourceItem(**s) for s in result["sources"]],
        latency_ms=result["latency_ms"],
        prompt_tokens=result["prompt_tokens"],
        completion_tokens=result["completion_tokens"],
    )


@app.post("/feedback")
def feedback(req: FeedbackRequest):
    try:
        feedback_id = submit_feedback(
            req.answer_id, req.rating, req.helpful, req.comment, req.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "recorded", "feedback_id": feedback_id}
