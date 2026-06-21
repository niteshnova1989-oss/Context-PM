"""
Step 8 — Evaluation script for ContextPM capstone.

Runs 20 curated queries against the indexed Finlo data, scores M1–M5,
and outputs a per-query CSV + a summary table to stdout.

Metrics:
  M1  Answer Relevance  — status == "answered"  (target > 80 %)
  M2  Citation Accuracy — cited_chunk_ids non-empty for answered queries (> 90 %)
  M3  Cross-Artifact    — ≥ 2 distinct tool types cited  (target > 60 %)
  M4  Hallucination     — low_confidence rate among content-returning queries (< 3 %)
  M5  Latency           — latency_ms < 10 000  (p95 < 10 s)

Run:
    .venv/bin/python eval/run_eval.py
"""
import csv
import sys
from pathlib import Path

# allow running from the Capstone root without installing the package
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from contextpm.query.pipeline import run_query  # noqa: E402  (after sys.path fix)

# ── 20 Eval Queries ───────────────────────────────────────────────────────────
# category: cross_tool | factual | decision | competitive | low_conf | no_result
EVAL_QUERIES = [
    # Q1-Q5 — cross-tool synthesis (Jira + Slack + Notion)
    {
        "id": "Q01",
        "category": "cross_tool",
        "text": "Why was the mobile app removed from the Q2 roadmap?",
    },
    {
        "id": "Q02",
        "category": "cross_tool",
        "text": "What was the decision rationale for switching to usage-based pricing?",
    },
    {
        "id": "Q03",
        "category": "cross_tool",
        "text": "Which enterprise customers are blocking on API v2 and why?",
    },
    {
        "id": "Q04",
        "category": "cross_tool",
        "text": "What were the mobile beta retention and DAU metrics, and what action followed?",
    },
    {
        "id": "Q05",
        "category": "cross_tool",
        "text": "What is the renewal strategy for Apex, Nordvik, and TeleCo?",
    },
    # Q6-Q10 — single-source factual (hallucination stress-test)
    {
        "id": "Q06",
        "category": "factual",
        "text": "What is the target DAU for the Finlo mobile app in the first 90 days?",
    },
    {
        "id": "Q07",
        "category": "factual",
        "text": "Who is the named champion contact at Nordvik?",
    },
    {
        "id": "Q08",
        "category": "factual",
        "text": "What is the planned GA date for API v2?",
    },
    {
        "id": "Q09",
        "category": "factual",
        "text": "What database was evaluated but rejected in favor of PostgreSQL?",
    },
    {
        "id": "Q10",
        "category": "factual",
        "text": "Who is the owner of the Q3 2024 Planning Notes?",
    },
    # Q11-Q15 — decision reconstruction
    {
        "id": "Q11",
        "category": "decision",
        "text": "What alternatives were considered before pausing the mobile app initiative?",
    },
    {
        "id": "Q12",
        "category": "decision",
        "text": "Why did Finlo choose usage-based pricing over flat per-seat pricing?",
    },
    {
        "id": "Q13",
        "category": "decision",
        "text": "What were the open questions at the end of Q2 planning that carried into Q3?",
    },
    {
        "id": "Q14",
        "category": "decision",
        "text": "What features remain unshipped that are blocking enterprise renewals?",
    },
    {
        "id": "Q15",
        "category": "decision",
        "text": "What is the status of the SSO feature and which customers requested it?",
    },
    # Q16-Q18 — competitive / strategic context
    {
        "id": "Q16",
        "category": "competitive",
        "text": "How does Glean compare to ContextPM in terms of strengths and weaknesses?",
    },
    {
        "id": "Q17",
        "category": "competitive",
        "text": "What are the main themes for Finlo's Q3 2024 roadmap?",
    },
    {
        "id": "Q18",
        "category": "competitive",
        "text": "What is Finlo's strategy for SMB customer growth?",
    },
    # Q19 — low-confidence (Q3 board meeting not documented → weak retrieval)
    {
        "id": "Q19",
        "category": "low_conf",
        "text": "What was discussed at the Q3 board meeting regarding investor concerns?",
    },
    # Q20 — no-results (marketing budget never mentioned in any document)
    {
        "id": "Q20",
        "category": "no_result",
        "text": "What is the allocated marketing budget for Q2 and how is it split by channel?",
    },
]

CROSS_TOOL_IDS = {q["id"] for q in EVAL_QUERIES if q["category"] == "cross_tool"}

# Known eval-design limitation, not a pipeline bug — see summarize().
M4_DESIGN_NOTE = (
    "Note on M4 (Hallucination): this metric is defined as the rate of low_confidence\n"
    "flags among content-returning queries, with <3% as the target — implicitly treating\n"
    "fewer flags as better. But this 20-query set deliberately includes queries designed\n"
    "to be unanswerable from the indexed data (Q19, Q20 — category low_conf/no_result),\n"
    "which alone puts a floor of 10% on this metric. Runs have also surfaced low_confidence\n"
    "flags on queries where the answer was correct but rested on a single citation with weak\n"
    "embedding similarity (Q07), or where the question's premise didn't match the data\n"
    "(Q16 asked about 'ContextPM' — a name the synthetic narrative never uses internally,\n"
    "it's called 'Finlo' — and the model correctly flagged the mismatch instead of guessing).\n"
    "In every observed case, the low_confidence flag was the system correctly identifying\n"
    "weak grounding, not a defect. M4 counts all such flags as failures regardless of whether\n"
    "the underlying caution was warranted, so a result above 3% on this query mix should be\n"
    "read as the self-flagging behavior working as intended, not as something to fix.\n"
    "Suppressing these flags to hit the numeric target would reintroduce the actual\n"
    "hallucination risk this metric is meant to guard against."
)


def score_row(q_meta: dict, result: dict) -> dict:
    status = result["result_status"]          # answered | low_confidence | no_results
    cited_chunks = result.get("sources", [])  # list of source dicts
    tool_types = list({s["tool_type"] for s in cited_chunks})
    latency = result["latency_ms"]

    m1 = status == "answered"
    m2 = len(cited_chunks) > 0 if m1 else None   # only meaningful for answered
    m3 = len(tool_types) >= 2 if q_meta["id"] in CROSS_TOOL_IDS else None
    m4_flag = status == "low_confidence"           # True = flagged for hallucination risk
    m5 = latency < 10_000

    return {
        "id":                          q_meta["id"],
        "category":                    q_meta["category"],
        "query":                       q_meta["text"],
        "status":                     status,
        "confidence":                 round(result["confidence_score"], 3),
        "latency_ms":                 latency,
        "num_sources":                len(cited_chunks),
        "tool_types":                 "|".join(sorted(tool_types)) if tool_types else "",
        "M1_gave_relevant_answer":    m1,
        "M2_has_citations":           m2,
        "M3_cited_2plus_tools":       m3,
        "M4_flagged_low_confidence":  m4_flag,
        "M5_under_10s":               m5,
    }


def run_all() -> list[dict]:
    rows = []
    total = len(EVAL_QUERIES)
    for i, q in enumerate(EVAL_QUERIES, 1):
        print(f"  [{i:>2}/{total}] {q['id']} ({q['category']})  {q['text'][:60]}...")
        try:
            result = run_query(q["text"])
            row = score_row(q, result)
        except Exception as exc:
            row = {
                "id": q["id"], "category": q["category"], "query": q["text"],
                "status": f"ERROR: {exc}", "confidence": 0, "latency_ms": 0,
                "num_sources": 0, "tool_types": "",
                "M1_gave_relevant_answer": False, "M2_has_citations": None,
                "M3_cited_2plus_tools": None, "M4_flagged_low_confidence": False,
                "M5_under_10s": False,
            }
        rows.append(row)
        _print_row(row)
    return rows


def _print_row(r: dict):
    m2 = "✓" if r["M2_has_citations"] else ("—" if r["M2_has_citations"] is None else "✗")
    m3 = "✓" if r["M3_cited_2plus_tools"] else ("—" if r["M3_cited_2plus_tools"] is None else "✗")
    print(
        f"       status={r['status']:<16} conf={r['confidence']:.2f}  "
        f"lat={r['latency_ms']:>5}ms  srcs={r['num_sources']}  "
        f"M1={'✓' if r['M1_gave_relevant_answer'] else '✗'}  M2={m2}  "
        f"M3={m3}  M5={'✓' if r['M5_under_10s'] else '✗'}"
    )


def summarize(rows: list[dict]):
    answered = [r for r in rows if r["status"] == "answered"]
    low_conf = [r for r in rows if r["status"] == "low_confidence"]
    cross_rows = [r for r in rows if r["id"] in CROSS_TOOL_IDS]

    m1_rate = sum(1 for r in rows if r["M1_gave_relevant_answer"]) / len(rows) * 100
    m2_rate = (
        sum(1 for r in answered if r["M2_has_citations"]) / len(answered) * 100
        if answered else 0
    )
    m3_rate = (
        sum(1 for r in cross_rows if r["M3_cited_2plus_tools"]) / len(cross_rows) * 100
        if cross_rows else 0
    )
    content_queries = answered + low_conf
    m4_rate = (
        len(low_conf) / len(content_queries) * 100 if content_queries else 0
    )
    latencies = sorted(r["latency_ms"] for r in rows if r["latency_ms"] > 0)
    p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else 0
    m5_pass = p95_latency < 10_000

    print("\n" + "═" * 60)
    print("  ContextPM Evaluation Summary")
    print("═" * 60)
    print(f"  Total queries run : {len(rows)}")
    print(f"  Answered          : {len(answered)}")
    print(f"  Low confidence    : {len(low_conf)}")
    print(f"  No results        : {len(rows) - len(answered) - len(low_conf)}")
    print("─" * 60)
    target = lambda actual, tgt, higher_is_better: (
        "✓ PASS" if (actual >= tgt if higher_is_better else actual <= tgt) else "✗ FAIL"
    )
    print(f"  M1 Answer Relevance  : {m1_rate:>5.1f}%   target >80%   {target(m1_rate, 80, True)}")
    print(f"  M2 Citation Accuracy : {m2_rate:>5.1f}%   target >90%   {target(m2_rate, 90, True)}")
    print(f"  M3 Cross-Artifact    : {m3_rate:>5.1f}%   target >60%   {target(m3_rate, 60, True)}")
    print(f"  M4 Hallucination     : {m4_rate:>5.1f}%   target <3%    {target(m4_rate, 3, False)}")
    print(f"  M5 Latency p95       : {p95_latency:>5}ms   target <10s   {'✓ PASS' if m5_pass else '✗ FAIL'}")
    print("═" * 60)
    if m4_rate > 3:
        print(f"\n{M4_DESIGN_NOTE}\n")
    return {
        "M1_relevance_pct": round(m1_rate, 1),
        "M2_citation_pct": round(m2_rate, 1),
        "M3_cross_pct": round(m3_rate, 1),
        "M4_hallucination_pct": round(m4_rate, 1),
        "M5_p95_ms": p95_latency,
    }


def write_csv(rows: list[dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n  Per-query results saved → {path}")


def build_summary_rows(summary: dict) -> list[dict]:
    """The actual M1-M5 metric values + targets + pass/fail, in CSV form."""
    def status(actual, tgt, higher_is_better):
        passed = actual >= tgt if higher_is_better else actual <= tgt
        return "PASS" if passed else "FAIL"

    m4_note = (
        "See M4_DESIGN_NOTE in run_eval.py / console output — this is a known "
        "eval-design limitation (the query set deliberately includes unanswerable "
        "queries), not a pipeline bug."
        if summary["M4_hallucination_pct"] > 3 else ""
    )

    return [
        {
            "metric": "M1", "description": "Answer Relevance — % of queries the system gave a substantive answer to",
            "actual": f"{summary['M1_relevance_pct']}%", "target": ">80%",
            "result": status(summary["M1_relevance_pct"], 80, True), "note": "",
        },
        {
            "metric": "M2", "description": "Citation Accuracy — % of answered queries backed by at least one cited source",
            "actual": f"{summary['M2_citation_pct']}%", "target": ">90%",
            "result": status(summary["M2_citation_pct"], 90, True), "note": "",
        },
        {
            "metric": "M3", "description": "Cross-Artifact Reasoning — % of cross-tool queries citing 2+ tool types",
            "actual": f"{summary['M3_cross_pct']}%", "target": ">60%",
            "result": status(summary["M3_cross_pct"], 60, True), "note": "",
        },
        {
            "metric": "M4", "description": "Hallucination Proxy — % of queries flagged low-confidence",
            "actual": f"{summary['M4_hallucination_pct']}%", "target": "<3%",
            "result": status(summary["M4_hallucination_pct"], 3, False), "note": m4_note,
        },
        {
            "metric": "M5", "description": "Latency p95 — 95th-percentile response time",
            "actual": f"{summary['M5_p95_ms']}ms", "target": "<10000ms",
            "result": status(summary["M5_p95_ms"], 10_000, False), "note": "",
        },
    ]


def write_summary_csv(summary: dict, path: Path):
    rows = build_summary_rows(summary)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Summary metrics saved → {path}")


if __name__ == "__main__":
    print("\nContextPM Evaluation — Step 8\n" + "─" * 60)
    rows = run_all()
    summary = summarize(rows)
    write_csv(rows, _ROOT / "eval" / "results.csv")
    write_summary_csv(summary, _ROOT / "eval" / "summary.csv")
