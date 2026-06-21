"""
FastAPI application for ContextPM.
Start: uvicorn contextpm.api.app:app --reload --port 8000
"""
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from contextpm.api.models import (
    FeedbackRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    SourceItem,
)
from contextpm.db.schema import get_conn, init_db
from contextpm.ingestion.pipeline import run_ingestion
from contextpm.query.pipeline import run_query

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
    if req.rating not in range(1, 6):
        raise HTTPException(status_code=400, detail="rating must be 1–5")

    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM answer WHERE id = ?", (req.answer_id,)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="answer_id not found")

    feedback_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO feedback
           (id, answer_id, user_id, rating, helpful, comment, created_at)
           VALUES (?,?,?,?,?,?,?)""",
        (
            feedback_id,
            req.answer_id,
            req.user_id,
            req.rating,
            int(req.helpful),
            req.comment,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return {"status": "recorded", "feedback_id": feedback_id}
