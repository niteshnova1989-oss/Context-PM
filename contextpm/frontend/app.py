"""
ContextPM — Streamlit frontend.
Run: streamlit run contextpm/frontend/app.py

Calls the query/ingestion pipelines directly (in-process) rather than going
through a separate API server — this is what lets the app run standalone on
Streamlit Cloud, which only runs one process per app. The FastAPI server in
contextpm/api/app.py still works as a standalone local demo of a real API;
it's just no longer something this frontend depends on.
"""
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Ensure project root is on sys.path when run via `streamlit run`
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from contextpm.config import IS_STREAMLIT_CLOUD, SQLITE_PATH
from contextpm.ingestion.pipeline import run_ingestion
from contextpm.query.pipeline import run_query, submit_feedback

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ContextPM",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset & chrome hide ───────────────────────────────────── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
header[data-testid="stHeader"]  { display: none !important; }
footer                           { display: none !important; }
#MainMenu                        { display: none !important; }
[data-testid="stDeployButton"]   { display: none !important; }
[data-testid="stDecoration"]     { display: none !important; }
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 860px !important;
}

/* ── Dark sidebar ──────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0A0A0A !important;
    border-right: none !important;
}
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.75) !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.08) !important; }
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: none !important;
    color: rgba(255,255,255,0.65) !important;
    text-align: left !important;
    width: 100% !important;
    font-size: 0.85rem !important;
    font-weight: 400 !important;
    padding: 0.45rem 0.75rem !important;
    border-radius: 6px !important;
    transition: all .15s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.07) !important;
    color: #FFFFFF !important;
}

/* ── Hero ──────────────────────────────────────────────────── */
.hero-eyebrow {
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: #2563EB; margin-bottom: 0.9rem;
}
.hero-title {
    font-size: 3rem; font-weight: 800; color: #0A0A0A;
    line-height: 1.08; letter-spacing: -0.03em;
    margin-bottom: 0.6rem;
}
.hero-sub {
    color: #6B7280; font-size: 1.05rem; font-weight: 400;
    line-height: 1.6; margin-bottom: 0.4rem;
}
.index-counts {
    font-size: 0.78rem; color: #9CA3AF; margin-bottom: 1.75rem;
}

/* ── Suggestion cards ──────────────────────────────────────── */
.query-card {
    background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px;
    padding: 0.75rem 1rem; margin-bottom: 0.45rem;
    font-size: 0.875rem; color: #374151;
    transition: border-color .15s ease, color .15s ease;
}
.query-card:hover { border-color: #2563EB; color: #1D4ED8; }

/* ── Answer card ───────────────────────────────────────────── */
.ans-card {
    background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;
    padding: 1.4rem 1.6rem; font-size: 0.9rem; line-height: 1.85;
    color: #1E293B; margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

/* ── Confidence bar ────────────────────────────────────────── */
.conf-bar-wrap { height: 4px; background: #F3F4F6; border-radius: 999px; margin: 0.35rem 0 0.75rem; }
.conf-bar-fill { height: 4px; border-radius: 999px; }

/* ── Source chips ──────────────────────────────────────────── */
.source-chip {
    display: inline-block; font-size: 0.72rem; font-weight: 600;
    padding: 0.18rem 0.55rem; border-radius: 4px;
    margin: 0.2rem 0.2rem 0.2rem 0; letter-spacing: 0.02em;
    border: 1px solid transparent;
}
.chip-jira   { background: #EFF6FF; color: #1D4ED8; border-color: #BFDBFE; }
.chip-slack  { background: #FDF2F8; color: #9D174D; border-color: #FBCFE8; }
.chip-notion { background: #F9FAFB; color: #374151; border-color: #E5E7EB; }

/* ── Banners ───────────────────────────────────────────────── */
.banner-warn {
    background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 8px;
    padding: 0.7rem 1rem; color: #78350F; font-size: 0.84rem; margin-bottom: 1rem;
}
.banner-err {
    background: #F9FAFB; border: 1px dashed #D1D5DB; border-radius: 10px;
    padding: 1.5rem; text-align: center; color: #6B7280;
    font-size: 0.88rem; margin-bottom: 1rem;
}

/* ── Decision trail ────────────────────────────────────────── */
.tl-item {
    border-left: 2px solid #E5E7EB; padding: 0 0 1.3rem 1.3rem;
    margin-left: 8px; position: relative;
}
.tl-item:last-child { border-left-color: transparent; }
.tl-dot {
    width: 12px; height: 12px; border-radius: 50%;
    position: absolute; left: -7px; top: 3px;
    border: 2px solid #FFFFFF;
}
.tl-card {
    background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px;
    padding: 0.85rem 1.1rem; font-size: 0.85rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.tl-date  { font-size: 0.72rem; color: #9CA3AF; letter-spacing: 0.02em; }
.tl-title { font-weight: 600; color: #0F172A; margin: 0.2rem 0; font-size: 0.875rem; }
.tl-body  { color: #6B7280; font-size: 0.82rem; line-height: 1.55; }

/* ── History rows ──────────────────────────────────────────── */
.hist-row {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 0.7rem 0.5rem; border-bottom: 1px solid #F3F4F6;
}
.hist-row:hover { background: #FAFAFA; border-radius: 6px; }
.hist-q    { font-size: 0.875rem; font-weight: 500; color: #0F172A; }
.hist-meta { font-size: 0.73rem; color: #9CA3AF; margin-top: 0.15rem; }

/* ── Settings rows ─────────────────────────────────────────── */
.settings-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.8rem 0; border-bottom: 1px solid #F3F4F6;
}
.settings-label { font-size: 0.875rem; font-weight: 500; color: #0F172A; }
.settings-sub   { font-size: 0.75rem; color: #6B7280; margin-top: 0.1rem; }

/* ── Metric (Latency) ──────────────────────────────────────── */
[data-testid="stMetricValue"] {
    white-space: nowrap !important; overflow: visible !important;
}

/* ── Section label ─────────────────────────────────────────── */
.section-label {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: #9CA3AF; margin: 1rem 0 0.4rem;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
_defaults = {
    "page": "home",
    "last_result": None,
    "feedback_submitted": False,
    "drill_source": None,   # source dict user clicked
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Helpers ────────────────────────────────────────────────────────────────────
TOOL_ICON  = {"jira": "🔵", "slack": "💬", "notion": "📝"}
CHIP_CLASS = {"jira": "chip-jira", "slack": "chip-slack", "notion": "chip-notion"}

def nav(page: str):
    st.session_state["page"] = page
    st.rerun()

def conf_bar_html(score: float) -> str:
    pct = int(score * 100)
    color = "#10B981" if score >= 0.6 else "#F59E0B" if score >= 0.4 else "#EF4444"
    return (
        f'<div class="conf-bar-wrap">'
        f'<div class="conf-bar-fill" style="width:{pct}%;background:{color}"></div>'
        f'</div>'
    )

def source_chip(tool: str, label: str) -> str:
    cls = CHIP_CLASS.get(tool, "chip-notion")
    icon = TOOL_ICON.get(tool, "📄")
    return f'<span class="source-chip {cls}">{icon} {label}</span>'

def db_conn():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_index_counts() -> dict:
    try:
        conn = db_conn()
        counts = {}
        for tool in ("jira", "slack", "notion"):
            row = conn.execute(
                "SELECT COUNT(*) as n FROM source WHERE tool_type=?", (tool,)
            ).fetchone()
            counts[tool] = row["n"] if row else 0
        conn.close()
        return counts
    except Exception:
        return {"jira": 0, "slack": 0, "notion": 0}

def get_source_detail(source_id: str) -> Optional[dict]:
    try:
        conn = db_conn()
        row = conn.execute(
            """SELECT s.title, s.tool_type, s.url, s.author,
                      s.created_at_source, s.updated_at_source,
                      c.content
               FROM source s
               JOIN chunk c ON c.source_id = s.id
               WHERE s.id = ?
               ORDER BY c.chunk_index LIMIT 1""",
            (source_id,),
        ).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None

def get_history(limit: int = 20) -> list:
    try:
        conn = db_conn()
        rows = conn.execute(
            """SELECT q.id, q.query_text, q.created_at,
                      a.result_status, a.confidence_score,
                      a.tool_types_cited, a.cited_source_ids,
                      a.latency_ms, a.id as answer_id
               FROM query q
               LEFT JOIN answer a ON a.query_id = q.id
               ORDER BY q.created_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        conn.close()
        result = []
        for r in rows:
            d = dict(r)
            d["tool_types_cited"] = json.loads(d["tool_types_cited"] or "[]")
            result.append(d)
        return result
    except Exception:
        return []

def get_feedback_for(answer_id: str) -> Optional[dict]:
    try:
        conn = db_conn()
        row = conn.execute(
            "SELECT rating, helpful FROM feedback WHERE answer_id=? LIMIT 1",
            (answer_id,),
        ).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None

# ── Cold-start auto-bootstrap ────────────────────────────────────────────────
# Streamlit Cloud's filesystem is ephemeral — a fresh deploy or wake-from-sleep
# starts with an empty contextpm.db (it's gitignored on purpose, see below).
# Auto-populate with the Finlo synthetic demo data — never real credentials,
# even if Jira/Slack/Notion secrets happen to be configured in this
# environment — so a public visitor always sees a working demo instead of an
# empty index. Idempotent: once source rows exist, every later rerun on this
# same container sees a non-zero count and skips straight past this.
if sum(get_index_counts().values()) == 0:
    with st.spinner("Setting up demo data…"):
        try:
            run_ingestion(force_synthetic=True)
        except Exception as e:
            st.error(f"Could not auto-populate demo data: {e}")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="font-size:1.1rem;font-weight:800;color:#FFFFFF;'
        'letter-spacing:-0.02em;padding:0.5rem 0 0.25rem">ContextPM</div>',
        unsafe_allow_html=True,
    )
    counts = get_index_counts()
    st.markdown(
        f'<div style="font-size:0.72rem;color:rgba(255,255,255,0.35);'
        f'margin-bottom:1rem">'
        f'{counts["jira"]} Jira · {counts["slack"]} Slack · {counts["notion"]} Notion'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    if st.button("Search",        use_container_width=True): nav("home")
    if st.button("History",       use_container_width=True): nav("history")
    st.markdown("---")
    if st.button("Connect Tools", use_container_width=True): nav("connect")
    if st.button("Settings",      use_container_width=True): nav("settings")
    st.markdown("---")
    st.markdown(
        '<div style="font-size:0.72rem;color:rgba(255,255,255,0.25);padding-top:0.25rem">'
        'nitesh@finlo.com · Finlo</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Home / Search
# ══════════════════════════════════════════════════════════════════════════════
def page_home():
    counts = get_index_counts()

    st.markdown('<div class="hero-eyebrow">Knowledge Search for PMs</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">Pull any thread.</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">'
        'Ask why a decision was made — ContextPM traces it across Jira, Slack, and Notion.'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="index-counts">'
        f'{counts["jira"]} Jira tickets · '
        f'{counts["slack"]} Slack threads · '
        f'{counts["notion"]} Notion pages indexed'
        f'</div>',
        unsafe_allow_html=True,
    )

    # st.text_input reruns the script on Enter, but that rerun is otherwise
    # indistinguishable from any other one — `go` below is only True on the
    # specific rerun the button click itself caused, so without this
    # on_change flag, pressing Enter updated the value but triggered nothing.
    def _mark_enter_pressed():
        st.session_state["search_enter_pressed"] = True

    query = st.text_input(
        "Ask a question",
        placeholder="e.g. Why did we drop the mobile app from Q2?",
        label_visibility="collapsed",
        key="search_box",
        on_change=_mark_enter_pressed,
    )

    col_btn, col_space = st.columns([1, 5])
    with col_btn:
        go = st.button("Search →", type="primary", use_container_width=True)

    enter_pressed = st.session_state.pop("search_enter_pressed", False)

    if (go or enter_pressed) and query.strip():
        _run_query(query.strip())
        return

    st.markdown('<div class="section-label">Suggested queries</div>', unsafe_allow_html=True)
    suggestions = [
        "Why did we drop the mobile app from Q2 roadmap?",
        "What changed between Pricing PRD v1 and v2?",
        "Why was the API v2 launch delayed?",
        "Who decided to switch to usage-based pricing and why?",
    ]
    for s in suggestions:
        c1, c2 = st.columns([10, 1])
        with c1:
            st.markdown(f'<div class="query-card">{s}</div>', unsafe_allow_html=True)
        with c2:
            clicked = st.button("→", key=f"sugg_{s[:25]}")
        if clicked:
            _run_query(s)
            return


def _run_query(query_text: str):
    result = None
    with st.status("Searching across tools…", expanded=True) as status:
        st.write("🔵 Querying Jira…")
        st.write("💬 Querying Slack…")
        st.write("📝 Querying Notion…")
        try:
            result = run_query(query_text)
            st.write("✅ Building answer with Claude Haiku…")
            status.update(label="Answer ready", state="complete", expanded=False)
        except Exception as e:
            status.update(label="Query failed", state="error")
            st.error(f"Query failed: {e}")
    if result:
        st.session_state["last_result"] = result
        st.session_state["feedback_submitted"] = False
        st.session_state["drill_source"] = None
        nav("results")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Results / Answer View + Source Drill-down
# ══════════════════════════════════════════════════════════════════════════════
def page_results():
    result = st.session_state.get("last_result")
    if not result:
        nav("home")
        return

    col_back, col_q = st.columns([1, 6])
    with col_back:
        if st.button("← New search"):
            nav("home")
    with col_q:
        st.markdown(f"**{result['query_text']}**")

    st.markdown("---")

    status = result["result_status"]
    score  = result["confidence_score"]
    sources = result.get("sources", [])

    # ── No results ─────────────────────────────────────────────────────────────
    if status == "no_results":
        st.markdown(
            '<div class="banner-err">'
            '<strong style="color:#374151">No relevant content found</strong><br>'
            'ContextPM searched Jira, Slack, and Notion but found nothing relevant.<br><br>'
            'Try rephrasing your question or using broader terms.'
            '</div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Try a different query", use_container_width=True):
                nav("home")
        with c2:
            if st.button("Search Jira only"):
                pass  # tool-filter is out of scope for capstone
        return

    # ── Low confidence banner ──────────────────────────────────────────────────
    if status == "low_confidence":
        st.markdown(
            '<div class="banner-warn">'
            '⚠️ <strong>Low confidence</strong> — retrieved content is weakly related. '
            'Verify against the cited sources before relying on this answer.'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Confidence + tool breakdown ────────────────────────────────────────────
    tool_counts: dict = {}
    for s in sources:
        tool_counts[s["tool_type"]] = tool_counts.get(s["tool_type"], 0) + 1

    col_conf, col_tools, col_lat = st.columns([2, 3, 2])
    with col_conf:
        st.markdown(f"**Confidence: {int(score * 100)}%**")
        st.markdown(conf_bar_html(score), unsafe_allow_html=True)
        # st.popover renders as a small inline button and opens as a floating
        # overlay — unlike st.expander it doesn't stretch this column's height
        # (which would otherwise leave col_tools/col_lat looking empty beside it).
        with st.popover("ⓘ how is this calculated?"):
            factors = result.get("confidence_factors") or {}
            if "weights" in factors:
                w = factors["weights"]
                tools_str = ", ".join(t.title() for t in factors["distinct_tools_cited"]) or "none"
                st.markdown(
                    f"- **Retrieval strength** — {int(factors['retrieval_strength']*100)}% "
                    f"(weight {int(w['retrieval_strength']*100)}%) — avg. similarity of the chunks "
                    f"the answer actually cites\n"
                    f"- **Source diversity** — {int(factors['source_diversity']*100)}% "
                    f"(weight {int(w['source_diversity']*100)}%) — {len(factors['distinct_tools_cited'])} of 3 "
                    f"tool types cited ({tools_str})\n"
                    f"- **Citation density** — {int(factors['citation_density']*100)}% "
                    f"(weight {int(w['citation_density']*100)}%) — {factors['citation_marks_total']} citation "
                    f"marks across {factors['distinct_sources_cited']} distinct source(s)"
                )
                st.caption(
                    "Confidence is a weighted blend of the three factors above, computed from "
                    "the model's actual cited answer — not just raw retrieval similarity."
                )
            else:
                st.caption(factors.get("reason", "No breakdown available for this answer."))
    with col_tools:
        badges = " ".join(
            source_chip(t, f"{t.title()} ×{n}")
            for t, n in sorted(tool_counts.items())
        )
        if badges:
            st.markdown(
                f'<div style="padding-top:.6rem">{badges}</div>',
                unsafe_allow_html=True,
            )
    with col_lat:
        st.metric("Latency", f"{result['latency_ms']}ms")

    # ── Answer ─────────────────────────────────────────────────────────────────
    # Escape "$" so Streamlit's markdown renderer doesn't treat dollar amounts
    # (e.g. "$485k") as LaTeX math delimiters.
    safe_answer = result["answer_text"].replace("$", "\\$")
    st.markdown(
        f'<div class="ans-card">{safe_answer}</div>',
        unsafe_allow_html=True,
    )

    # ── Sources with drill-down (s9 modal equivalent) ──────────────────────────
    if sources:
        st.markdown("**Sources**")
        for s in sources:
            icon = TOOL_ICON.get(s["tool_type"], "📄")
            # Bracket numbers match the inline [n] citations in the answer
            # above — a source can carry more than one if it was retrieved
            # as multiple chunks (e.g. "[1][3]").
            nums = "".join(f"[{n}]" for n in s.get("citation_numbers", []))
            label = f"{nums} {icon} [{s['tool_type'].upper()}] {s['title']}".strip()
            with st.expander(label):
                detail = get_source_detail(s["source_id"])
                if detail:
                    meta_cols = st.columns(3)
                    with meta_cols[0]:
                        st.caption(f"**Tool:** {detail['tool_type'].upper()}")
                    with meta_cols[1]:
                        date = (detail["created_at_source"] or "")[:10]
                        st.caption(f"**Date:** {date}")
                    with meta_cols[2]:
                        st.caption(f"**Author:** {detail['author'] or '—'}")
                    st.markdown("**Matched content:**")
                    st.markdown(
                        f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
                        f'border-radius:8px;padding:12px;font-size:.85rem;'
                        f'line-height:1.7;color:#374151;max-height:240px;overflow-y:auto">'
                        f'{detail["content"]}</div>',
                        unsafe_allow_html=True,
                    )
                    # The source link points into the real Jira/Slack/Notion
                    # workspace — only the app owner running locally is
                    # logged into those accounts, so showing it to public
                    # demo visitors would just be a dead end.
                    if IS_STREAMLIT_CLOUD:
                        st.caption("🔒 Source link hidden in the public demo")
                    else:
                        st.markdown(
                            f'<a href="{s["url"]}" target="_blank" '
                            f'style="font-size:.8rem">Open in {s["tool_type"].title()} ↗</a>',
                            unsafe_allow_html=True,
                        )
                elif not IS_STREAMLIT_CLOUD:
                    st.caption(f"[{s['url']}]({s['url']})")

    # ── Action bar (matches wireframe s7 fb-bar) ───────────────────────────────
    st.markdown("")
    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("🧵 See Decision Trail", type="primary", use_container_width=True):
            nav("trail")
    with a2:
        if st.button("👍 / 👎  Give Feedback", use_container_width=True):
            nav("feedback")
    with a3:
        st.download_button(
            "⬇ Export answer",
            data=result["answer_text"],
            file_name="contextpm_answer.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with st.expander("Token usage"):
        st.caption(
            f"Prompt: {result['prompt_tokens']} tokens  · "
            f"Completion: {result['completion_tokens']} tokens  · "
            f"Model: {result.get('answer_id', '')[:8]}…"
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Decision Trail  (wireframe s8 — timeline)
# ══════════════════════════════════════════════════════════════════════════════
def page_trail():
    result = st.session_state.get("last_result")
    if not result:
        nav("home")
        return

    if st.button("← Back to answer"):
        nav("results")

    sources = result.get("sources", [])

    st.markdown("## 🧵 Decision Trail")
    st.markdown(
        f"How **\"{result['query_text']}\"** evolved across your tools"
    )
    st.markdown("---")

    if not sources:
        st.info("No sources were cited — trail not available.")
        return

    # Enrich sources with dates from SQLite
    enriched = []
    for s in sources:
        detail = get_source_detail(s["source_id"])
        if detail:
            enriched.append({**s, **detail})
        else:
            enriched.append({**s, "created_at_source": "", "content": "", "author": ""})

    # Sort chronologically
    def parse_date(d):
        raw = d.get("created_at_source") or ""
        try:
            return datetime.fromisoformat(raw[:19])
        except Exception:
            return datetime.min

    enriched.sort(key=parse_date)

    TOOL_DOT_COLOR = {"jira": "#2563EB", "slack": "#BE185D", "notion": "#374151"}
    TOOL_STEP_LABEL = {
        "notion": ("📄 Document context",    "Notion page"),
        "jira":   ("📋 Ticket / record",     "Jira ticket"),
        "slack":  ("💬 Team discussion",     "Slack thread"),
    }

    total = len(enriched)
    date_range = ""
    dates = [parse_date(s) for s in enriched if parse_date(s) != datetime.min]
    if dates:
        d0, d1 = min(dates).strftime("%b %d"), max(dates).strftime("%b %d, %Y")
        date_range = f"{d0} – {d1}"

    st.caption(f"{total} event{'s' if total != 1 else ''}" + (f" · {date_range}" if date_range else ""))
    st.markdown("")

    for i, s in enumerate(enriched):
        tool = s.get("tool_type", "notion")
        dot_color = TOOL_DOT_COLOR.get(tool, "#94A3B8")
        chip_cls = CHIP_CLASS.get(tool, "chip-notion")
        icon = TOOL_ICON.get(tool, "📄")
        step_label, step_type = TOOL_STEP_LABEL.get(tool, ("📌 Source", ""))
        date_str = (s.get("created_at_source") or "")[:10]
        author = s.get("author") or "—"
        snippet = (s.get("content") or "")[:180].replace("\n", " ").strip()
        if len(s.get("content", "")) > 180:
            snippet += "…"

        st.markdown(
            f'<div class="tl-item">'
            f'  <div class="tl-dot" style="background:{dot_color}"></div>'
            f'  <div class="tl-card">'
            f'    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.3rem">'
            f'      <span class="source-chip {chip_cls}">{icon} {s["title"]}</span>'
            f'      <span class="tl-date">{date_str}</span>'
            f'    </div>'
            f'    <div class="tl-title">Step {i+1} — {step_label}</div>'
            f'    <div class="tl-body">{snippet}</div>'
            f'    <div style="margin-top:.4rem;font-size:.76rem;color:#94A3B8">by {author}</div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.caption(
        "Trail reconstructed from cited sources only. "
        "Ordered by source creation date. "
        "Not all intermediate steps may be represented."
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Feedback
# ══════════════════════════════════════════════════════════════════════════════
def page_feedback():
    result = st.session_state.get("last_result")
    if not result:
        nav("home")
        return

    if st.button("← Back to answer"):
        nav("results")

    st.markdown("## Give Feedback")
    st.markdown(f"*{result['query_text']}*")
    st.markdown("---")

    if st.session_state.get("feedback_submitted"):
        st.success("Thanks — your feedback has been recorded!")
        if st.button("Ask another question"):
            nav("home")
        return

    with st.form("feedback_form"):
        rating  = st.slider("How useful was this answer?", 1, 5, 4,
                             help="1 = not useful, 5 = very useful")
        helpful = st.checkbox("This answer was helpful", value=True)
        comment = st.text_area("Comments (optional)",
                               placeholder="What was missing or incorrect?")
        submitted = st.form_submit_button("Submit feedback", type="primary")

    if submitted:
        try:
            submit_feedback(result["answer_id"], rating, helpful, comment or None)
            st.session_state["feedback_submitted"] = True
            st.rerun()
        except (ValueError, LookupError) as e:
            st.error(f"Could not save feedback: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Query History  (wireframe s10)
# ══════════════════════════════════════════════════════════════════════════════
def page_history():
    st.markdown("## 🕐 Query History")
    st.markdown("---")

    history = get_history(50)
    if not history:
        st.info("No queries yet — your history will appear here after your first search.")
        if st.button("Ask your first question"):
            nav("home")
        return

    search_filter = st.text_input("Search history…", label_visibility="collapsed",
                                  placeholder="Filter queries…")
    if search_filter:
        history = [h for h in history if search_filter.lower() in h["query_text"].lower()]

    # Group by date
    def date_group(ts: str) -> str:
        if not ts:
            return "Earlier"
        try:
            dt = datetime.fromisoformat(ts[:19].replace("Z", ""))
            today = datetime.utcnow().date()
            d = dt.date()
            delta = (today - d).days
            if delta == 0:   return "Today"
            if delta == 1:   return "Yesterday"
            if delta < 7:    return "Last 7 days"
            if delta < 30:   return "Last 30 days"
            return dt.strftime("%B %Y")
        except Exception:
            return "Earlier"

    groups: dict = {}
    for h in history:
        g = date_group(h["created_at"])
        groups.setdefault(g, []).append(h)

    for group_label, items in groups.items():
        st.markdown(
            f'<div class="section-label" style="margin:.8rem 0 .3rem">{group_label}</div>',
            unsafe_allow_html=True,
        )
        for h in items:
            tools = h["tool_types_cited"] or []
            tool_badges = " ".join(
                source_chip(t, t.title())
                for t in sorted(set(tools))
            )
            fb = get_feedback_for(h.get("answer_id") or "")
            fb_label = ""
            if fb:
                fb_label = (
                    '<span style="font-size:.75rem;color:#22C55E">👍 Helpful</span>'
                    if fb["helpful"]
                    else '<span style="font-size:.75rem;color:#EF4444">👎 Not helpful</span>'
                )
            status_color = {
                "answered": "#22C55E",
                "low_confidence": "#F59E0B",
                "no_results": "#EF4444",
            }.get(h.get("result_status") or "", "#94A3B8")

            st.markdown(
                f'<div class="hist-row">'
                f'  <div style="flex:1">'
                f'    <div class="hist-q">{h["query_text"]}</div>'
                f'    <div style="margin-top:.25rem">{tool_badges} {fb_label}</div>'
                f'  </div>'
                f'  <div style="text-align:right;min-width:80px">'
                f'    <div class="hist-meta">{(h["created_at"] or "")[:10]}</div>'
                f'    <div style="width:8px;height:8px;border-radius:50%;'
                f'background:{status_color};display:inline-block;margin-top:4px"></div>'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            # Clickable re-run button per row
            if st.button("Re-run →", key=f"hist_{h['id']}"):
                _run_query(h["query_text"])
                return


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Connect Tools  (wireframe s3 + s5)
# ══════════════════════════════════════════════════════════════════════════════
def page_connect():
    counts = get_index_counts()

    st.markdown("## 🔌 Connect Tools")

    # Step indicator
    st.markdown("""
    <div style="display:flex;align-items:center;gap:6px;margin:1rem 0 1.5rem;font-size:.8rem">
      <div style="background:#22C55E;color:#fff;border-radius:50%;width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-weight:700">✓</div>
      <span style="color:#22C55E;font-weight:600">Connect</span>
      <div style="height:2px;width:30px;background:#22C55E"></div>
      <div style="background:#22C55E;color:#fff;border-radius:50%;width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-weight:700">✓</div>
      <span style="color:#22C55E;font-weight:600">Select</span>
      <div style="height:2px;width:30px;background:#22C55E"></div>
      <div style="background:#22C55E;color:#fff;border-radius:50%;width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-weight:700">✓</div>
      <span style="color:#22C55E;font-weight:600">Index</span>
      <div style="height:2px;width:30px;background:#22C55E"></div>
      <div style="background:#2563EB;color:#fff;border-radius:50%;width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-weight:700">4</div>
      <span style="color:#2563EB;font-weight:600">Ready</span>
    </div>
    """, unsafe_allow_html=True)

    # Connected tools (all green since already indexed)
    st.markdown("**Connected tools**")
    c1, c2, c3 = st.columns(3)
    for col, (tool, icon, label) in zip(
        [c1, c2, c3],
        [("jira", "🔵", "Jira"), ("slack", "💬", "Slack"), ("notion", "📝", "Notion")],
    ):
        with col:
            n = counts.get(tool, 0)
            st.markdown(
                f'<div style="border:2px solid #22C55E;border-radius:12px;padding:1rem;'
                f'text-align:center;background:#F0FDF4">'
                f'<div style="font-size:2rem">{icon}</div>'
                f'<div style="font-weight:700;font-size:.9rem;margin:.3rem 0">{label}</div>'
                f'<div style="font-size:.75rem;color:#15803D">✓ Connected</div>'
                f'<div style="font-size:.72rem;color:#64748B;margin-top:.2rem">{n} items</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("**Re-run indexing**")
    st.caption("Scans all data files and rebuilds the vector index.")

    if st.button("🔄 Re-index now", type="primary"):
        with st.status("Indexing…", expanded=True) as status:
            st.write("🔵 Processing Jira tickets…")
            st.write("💬 Processing Slack threads…")
            st.write("📝 Processing Notion pages…")
            try:
                stats = run_ingestion()
                status.update(label="Indexing complete", state="complete", expanded=False)
                st.success(
                    f"Done — {stats['sources']} sources, "
                    f"{stats['chunks']} chunks indexed."
                )
            except Exception as e:
                status.update(label="Indexing failed", state="error")
                st.error(f"Error: {e}")

    st.markdown("---")
    st.caption(
        "🔒 Read-only access only. ContextPM never writes to your tools. "
        "OAuth tokens are stored encrypted and can be revoked at any time."
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Settings  (wireframe s11)
# ══════════════════════════════════════════════════════════════════════════════
def page_settings():
    counts = get_index_counts()

    # Real query/answer counts
    try:
        conn = db_conn()
        q_count = conn.execute("SELECT COUNT(*) as n FROM query").fetchone()["n"]
        a_count = conn.execute("SELECT COUNT(*) as n FROM answer").fetchone()["n"]
        fb_count = conn.execute("SELECT COUNT(*) as n FROM feedback").fetchone()["n"]
        conn.close()
    except Exception:
        q_count = a_count = fb_count = 0

    st.markdown("## ⚙️ Settings")
    st.markdown("---")

    # Connected tools
    st.markdown('<div class="section-label">Connected Tools</div>', unsafe_allow_html=True)
    for tool, icon, label in [("jira", "🔵", "Jira"), ("slack", "💬", "Slack"), ("notion", "📝", "Notion")]:
        n = counts.get(tool, 0)
        st.markdown(
            f'<div class="settings-row">'
            f'  <div style="display:flex;align-items:center;gap:10px">'
            f'    <span style="font-size:1.2rem">{icon}</span>'
            f'    <div>'
            f'      <div class="settings-label">{label}</div>'
            f'      <div class="settings-sub">finlo · {n} items indexed</div>'
            f'    </div>'
            f'  </div>'
            f'  <span style="font-size:.75rem;font-weight:600;padding:.2rem .6rem;'
            f'border-radius:999px;background:#DCFCE7;color:#15803D">● Connected</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    # Usage stats
    st.markdown('<div class="section-label" style="margin:.5rem 0">Usage</div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Queries run", q_count)
    with m2: st.metric("Answers generated", a_count)
    with m3: st.metric("Feedback given", fb_count)

    st.markdown("")

    # Model settings (read-only for capstone)
    st.markdown('<div class="section-label" style="margin:.5rem 0">Model Configuration</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        st.selectbox("LLM", ["claude-haiku-4-5-20251001"], disabled=True,
                     help="Changing models requires restarting the API server.")
    with col_b:
        st.selectbox("Embeddings", ["all-MiniLM-L6-v2 (local, 384-dim)"], disabled=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.slider("Top-K chunks", 4, 16, 8, disabled=True,
                  help="Number of chunks retrieved per query.")
    with col_d:
        st.slider("Confidence threshold", 0.1, 0.9, 0.5, step=0.05, disabled=True,
                  help="Below this score the answer is flagged as low-confidence.")

    st.markdown("")

    # Account
    st.markdown('<div class="section-label" style="margin:.5rem 0">Account</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="settings-row">'
        '  <div><div class="settings-label">nitesh@finlo.com</div>'
        '     <div class="settings-sub">PM at Finlo · Free plan</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("")

    # Backend health
    st.markdown('<div class="section-label" style="margin:.5rem 0">Backend</div>', unsafe_allow_html=True)
    st.code("Mode: direct (in-process) — no separate API server required", language=None)
    if st.button("Check database connection"):
        try:
            conn = db_conn()
            conn.execute("SELECT 1")
            conn.close()
            st.success("Database reachable.")
        except Exception as e:
            st.error(f"Database error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# Router
# ══════════════════════════════════════════════════════════════════════════════
_page = st.session_state["page"]
if   _page == "home":     page_home()
elif _page == "results":  page_results()
elif _page == "trail":    page_trail()
elif _page == "feedback": page_feedback()
elif _page == "history":  page_history()
elif _page == "connect":  page_connect()
elif _page == "settings": page_settings()
else: page_home()
