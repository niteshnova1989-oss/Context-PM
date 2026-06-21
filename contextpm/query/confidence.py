"""
Step 4.5 / Step 7.5 from Phase 2 query flow.

Confidence blends three signals computed *after* the LLM has answered and
its citations have been parsed — a single retrieved chunk's similarity score
says nothing about whether the answer is actually well-grounded:

  - retrieval_strength — avg similarity of the chunks the LLM actually cited
                         (not just the single best-retrieved chunk)
  - source_diversity   — how many distinct tools (jira/slack/notion) the
                         cited evidence spans, rewarding cross-tool
                         corroboration instead of ignoring it
  - citation_density   — how often the answer re-references its cited
                         sources (citations per distinct source), as a proxy
                         for how thoroughly each claim is grounded

If nothing was retrieved, or the LLM cited nothing, falls back to the raw
top-chunk retrieval score so there's always a defined number.
"""
import re

from contextpm.config import LOW_CONFIDENCE_THRESHOLD

WEIGHTS = {
    "retrieval_strength": 0.45,
    "source_diversity":   0.35,
    "citation_density":   0.20,
}


def compute_confidence(
    chunks: list[dict],
    cited_chunk_ids: list[str],
    cited_source_ids: list[str],
    tool_types_cited: list[str],
    answer_text: str,
) -> tuple[float, dict]:
    """Returns (confidence_score, factors) for display + the gating decision."""
    if not chunks:
        return 0.0, {"reason": "no chunks retrieved"}

    if not cited_chunk_ids:
        # LLM didn't ground its answer in any retrieved chunk — fall back to
        # the raw top-chunk similarity rather than rewarding zero citations.
        score = chunks[0]["score"]
        return score, {
            "reason": "no citations parsed from answer — using raw top-chunk retrieval score",
            "retrieval_strength": score,
        }

    cited_scores = [c["score"] for c in chunks if c["chunk_id"] in cited_chunk_ids]
    retrieval_strength = sum(cited_scores) / len(cited_scores)

    distinct_tools = sorted(set(tool_types_cited))
    source_diversity = min(len(distinct_tools) / 3, 1.0)

    distinct_sources = max(1, len(set(cited_source_ids)))
    citation_marks_total = len(re.findall(r"\[\d+\]", answer_text))
    citation_density = min((citation_marks_total / distinct_sources) / 3, 1.0)

    score = (
        WEIGHTS["retrieval_strength"] * retrieval_strength
        + WEIGHTS["source_diversity"] * source_diversity
        + WEIGHTS["citation_density"] * citation_density
    )
    score = round(min(max(score, 0.0), 1.0), 4)

    factors = {
        "retrieval_strength":     round(retrieval_strength, 3),
        "source_diversity":       round(source_diversity, 3),
        "citation_density":       round(citation_density, 3),
        "distinct_tools_cited":   distinct_tools,
        "distinct_sources_cited": distinct_sources,
        "citation_marks_total":   citation_marks_total,
        "weights":                WEIGHTS,
    }
    return score, factors


def status_for_score(score: float) -> str:
    return "low_confidence" if score < LOW_CONFIDENCE_THRESHOLD else "answered"
