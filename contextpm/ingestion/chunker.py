"""
Tool-specific chunking strategies from Phase 2 design:
  Jira   — 1 chunk per ticket (title + description + all comments)
  Slack  — 1 chunk per thread (all messages concatenated)
  Notion — sliding window, 450 tokens, 50-token overlap, per document segment
"""
import tiktoken

_enc = tiktoken.get_encoding("cl100k_base")

# Inserted by loader.py's blocks_to_text() wherever a Notion 'divider' block
# appears. A single Notion page can contain multiple unrelated documents
# (e.g. a multi-doc markdown import) separated by dividers — splitting on
# this marker before windowing keeps the sliding window from straddling two
# documents. \x1e (ASCII Record Separator) won't appear in real text and
# pages with no dividers just yield one segment, so normal single-document
# pages chunk exactly as before.
DOC_BOUNDARY_MARKER = "\x1e"


def _count(text: str) -> int:
    return len(_enc.encode(text))


def _make_chunk(content, index, tool_type, title, url, author, created_at_source):
    return {
        "content": content,
        "chunk_index": index,
        "token_count": _count(content),
        "metadata": {
            "tool_type": tool_type,
            "title": title,
            "url": url,
            "author": author or "",
            "created_at_source": created_at_source or "",
        },
    }


def chunk_jira(ticket: dict) -> list[dict]:
    parts = [
        f"Ticket: {ticket['external_id']}",
        f"Title: {ticket['title']}",
        f"Status: {ticket['status']}",
        f"Description: {ticket['description']}",
    ]
    for c in ticket.get("comments", []):
        parts.append(f"Comment by {c['author']} ({c['created_at']}): {c['body']}")
    content = "\n\n".join(parts)
    return [_make_chunk(content, 0, "jira", ticket["title"],
                        ticket["url"], ticket["author"], ticket["created_at"])]


def chunk_slack(thread: dict) -> list[dict]:
    parts = [f"Channel: {thread['channel']}"]
    for m in thread["messages"]:
        parts.append(f"{m['author']} [{m['ts']}]: {m['text']}")
    content = "\n".join(parts)
    first = thread["messages"][0]
    title = f"{thread['channel']} — {first['ts'][:10]}"
    return [_make_chunk(content, 0, "slack", title,
                        thread["url"], first["author"], first["ts"])]


def _sliding_window(text: str, start_index: int, max_tokens: int, overlap: int,
                     title, url, author, created_at) -> list[dict]:
    tokens = _enc.encode(text)
    if not tokens:
        return []

    step = max_tokens - overlap
    out = []
    i = 0
    while i < len(tokens):
        window = tokens[i: i + max_tokens]
        content = _enc.decode(window)
        out.append(_make_chunk(content, start_index + len(out), "notion",
                                title, url, author, created_at))
        i += step

    return out


def chunk_notion(page: dict, max_tokens: int = 450, overlap: int = 50) -> list[dict]:
    segments = [s.strip("\n") for s in page["content"].split(DOC_BOUNDARY_MARKER)]
    segments = [s for s in segments if s.strip()]

    chunks = []
    for seg in segments:
        chunks.extend(_sliding_window(
            seg, len(chunks), max_tokens, overlap,
            page["title"], page["url"], page["author"], page["created_at"],
        ))
    return chunks


CHUNKERS = {
    "jira":   chunk_jira,
    "slack":  chunk_slack,
    "notion": chunk_notion,
}
