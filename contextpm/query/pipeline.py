"""
Full query flow (Phase 2 Section 6.2 Steps 1-9).
Run: python -m contextpm.query.pipeline "your question here"
"""
import json
import re
import time
import uuid
from datetime import datetime, timezone

import anthropic

from contextpm.config import ANTHROPIC_API_KEY, LLM_MODEL
from contextpm.db.schema import get_conn, init_db
from contextpm.query.confidence import compute_confidence, status_for_score
from contextpm.query.retriever import retrieve

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are ContextPM, a knowledge assistant for product managers.

Answer the question using ONLY the context chunks provided below.
Cite every factual claim inline using [1], [2], etc. — the number matches the source label.
If a fact appears in multiple sources, cite all relevant ones.
Do not add information that is not present in the context.
If the context is insufficient, say so explicitly rather than guessing.

Citation format is strict:
- A citation is a bare [n] placed immediately after the sentence or clause it
  supports, e.g.: Mobile was paused due to API v2 staffing conflicts [1][3].
- Never wrap the claim text itself in brackets, e.g. NOT:
  [Mobile was paused due to API v2 staffing conflicts][1]
- Never put other text inside the brackets — only the digit(s)."""

LOW_CONF_PREFIX = (
    "⚠️ Low confidence — the retrieved content is weakly related to your query. "
    "Verify this answer against the cited sources before relying on it.\n\n"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_context(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        date = c["created_at_source"][:10] if c["created_at_source"] else ""
        header = f"[{i}] {c['title']} ({c['tool_type'].upper()})"
        if date:
            header += f" — {date}"
        parts.append(f"{header}\n{c['content']}")
    return "\n\n---\n\n".join(parts)


def _parse_citations(answer_text: str, chunks: list[dict]) -> tuple[list[str], list[str], list[str]]:
    """Extract [N] refs → chunk_ids, source_ids, tool_types."""
    indices = {int(n) - 1 for n in re.findall(r"\[(\d+)\]", answer_text)}
    cited_chunks, cited_sources, cited_tools = [], [], []
    seen_sources = set()
    for i in sorted(indices):
        if 0 <= i < len(chunks):
            c = chunks[i]
            cited_chunks.append(c["chunk_id"])
            if c["source_id"] not in seen_sources:
                cited_sources.append(c["source_id"])
                cited_tools.append(c["tool_type"])
                seen_sources.add(c["source_id"])
    return cited_chunks, cited_sources, cited_tools


def run_query(query_text: str, user_id: str = None) -> dict:
    init_db()
    conn = get_conn()

    # resolve user
    if not user_id:
        row = conn.execute(
            "SELECT id FROM user WHERE email = 'nitesh@finlo.com'"
        ).fetchone()
        user_id = row["id"] if row else None

    # Step 2 — save Query row
    query_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO query (id, user_id, query_text, created_at) VALUES (?,?,?,?)",
        (query_id, user_id, query_text, _now()),
    )
    conn.commit()

    # Steps 3 & 4 — embed + retrieve
    t0 = time.time()
    chunks = retrieve(query_text)

    answer_text = ""
    prompt_tokens = completion_tokens = 0

    if not chunks:
        result_status = "no_results"
        confidence_score, confidence_factors = 0.0, {"reason": "no chunks retrieved"}
        answer_text = (
            "No relevant content found across the indexed Jira tickets, "
            "Slack threads, and Notion pages for this query."
        )
        cited_chunk_ids = cited_source_ids = tool_types_cited = []

    else:
        # Step 5 — build prompt
        context = _build_context(chunks)
        user_message = f"CONTEXT:\n\n{context}\n\nQUESTION: {query_text}"

        # Step 6 — call LLM
        response = _client.messages.create(
            model=LLM_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        raw_answer = response.content[0].text
        prompt_tokens = response.usage.input_tokens
        completion_tokens = response.usage.output_tokens

        # Step 7 — parse citations
        cited_chunk_ids, cited_source_ids, tool_types_cited = _parse_citations(
            raw_answer, chunks
        )

        # Step 7.5 — confidence, computed from the actual grounded answer
        # (retrieval similarity of *cited* chunks + cross-tool corroboration +
        # citation density) rather than a single raw retrieval score.
        confidence_score, confidence_factors = compute_confidence(
            chunks, cited_chunk_ids, cited_source_ids, tool_types_cited, raw_answer
        )
        # Zero citations means the LLM couldn't ground its answer in anything
        # retrieved — that's never "answered", regardless of raw retrieval score.
        result_status = (
            "low_confidence" if not cited_chunk_ids else status_for_score(confidence_score)
        )

        answer_text = (
            LOW_CONF_PREFIX + raw_answer
            if result_status == "low_confidence"
            else raw_answer
        )

    latency_ms = int((time.time() - t0) * 1000)

    # Step 8 — save Answer row
    answer_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO answer
           (id, query_id, answer_text, cited_chunk_ids, cited_source_ids,
            tool_types_cited, latency_ms, model_used, prompt_tokens,
            completion_tokens, confidence_score, result_status, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            answer_id, query_id, answer_text,
            json.dumps(cited_chunk_ids),
            json.dumps(cited_source_ids),
            json.dumps(tool_types_cited),
            latency_ms, LLM_MODEL, prompt_tokens, completion_tokens,
            confidence_score, result_status, _now(),
        ),
    )
    conn.commit()

    # Step 9 — return
    # cited_source_ids/tool_types_cited are already deduped 1:1 per source (see
    # _parse_citations) — zipping against cited_chunk_ids (one entry per citation,
    # not deduped) would mismatch whenever a source has more than one cited chunk.
    sources = []
    for source_id, tool_type in zip(cited_source_ids, tool_types_cited):
        chunk = next((c for c in chunks if c["source_id"] == source_id), None)
        if chunk:
            sources.append({
                "chunk_id":  chunk["chunk_id"],
                "source_id": source_id,
                "tool_type": tool_type,
                "title":     chunk["title"],
                "url":       chunk["url"],
                "dataset":   chunk["dataset"],
            })

    conn.close()

    return {
        "answer_id":        answer_id,
        "query_text":       query_text,
        "answer_text":      answer_text,
        "result_status":      result_status,
        "confidence_score":   confidence_score,
        "confidence_factors": confidence_factors,
        "sources":          sources,
        "latency_ms":       latency_ms,
        "prompt_tokens":    prompt_tokens,
        "completion_tokens": completion_tokens,
    }


def submit_feedback(answer_id: str, rating: int, helpful: bool,
                     comment: str = None, user_id: str = None) -> str:
    """Records feedback on an answer. Shared by the FastAPI /feedback
    endpoint and the frontend's direct-call path, so the two never drift.
    Raises ValueError for a bad rating, LookupError if answer_id doesn't
    exist."""
    if rating not in range(1, 6):
        raise ValueError("rating must be 1-5")

    conn = get_conn()
    row = conn.execute("SELECT id FROM answer WHERE id = ?", (answer_id,)).fetchone()
    if not row:
        conn.close()
        raise LookupError("answer_id not found")

    feedback_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO feedback
           (id, answer_id, user_id, rating, helpful, comment, created_at)
           VALUES (?,?,?,?,?,?,?)""",
        (feedback_id, answer_id, user_id, rating, int(helpful), comment, _now()),
    )
    conn.commit()
    conn.close()
    return feedback_id


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "Why did we drop the mobile app from Q2?"
    result = run_query(q)
    print(f"\nQ: {result['query_text']}")
    print(f"Status: {result['result_status']}  |  Confidence: {result['confidence_score']}  |  Latency: {result['latency_ms']}ms\n")
    print(result["answer_text"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"  [{s['tool_type'].upper()}] {s['title']}  {s['url']}")
