"""
Data loaders for Jira, Slack, and Notion.

If real API credentials are present in .env, fetches live data from the
actual tool accounts. Falls back to synthetic JSON files if any credential
is missing — so the app works during local dev without all three tokens.
"""
import json
import base64
from pathlib import Path

import requests

from contextpm.config import (
    SYNTHETIC_DATA_PATH,
    JIRA_DOMAIN, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT,
    SLACK_BOT_TOKEN,
    NOTION_TOKEN, NOTION_PARENT_PAGE_ID,
)
from contextpm.ingestion.chunker import DOC_BOUNDARY_MARKER


# ══════════════════════════════════════════════════════════════════════════════
# JIRA
# ══════════════════════════════════════════════════════════════════════════════

def _jira_headers() -> dict:
    token = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Accept": "application/json"}


def _adf_to_text(node) -> str:
    """Recursively extract plain text from Atlassian Document Format (ADF)."""
    if not node or not isinstance(node, dict):
        return ""
    if node.get("type") == "text":
        return node.get("text", "")
    joiner = "\n" if node.get("type") in (
        "doc", "paragraph", "heading", "blockquote",
        "bulletList", "orderedList", "listItem",
    ) else " "
    parts = [_adf_to_text(child) for child in node.get("content", [])]
    return joiner.join(p for p in parts if p)


def load_jira(force_synthetic: bool = False) -> list[dict]:
    if force_synthetic or not all([JIRA_DOMAIN, JIRA_EMAIL, JIRA_API_TOKEN]):
        print("  [loader] Jira: using synthetic data" if force_synthetic else
              "  [loader] Jira: credentials not set — using synthetic data")
        return json.loads((SYNTHETIC_DATA_PATH / "jira_tickets.json").read_text())

    base = f"https://{JIRA_DOMAIN}.atlassian.net/rest/api/3"
    params = {
        "jql":    f"project={JIRA_PROJECT} ORDER BY created ASC",
        "maxResults": 50,
        "fields": "summary,description,status,assignee,reporter,created,updated,comment",
    }
    try:
        # Atlassian deprecated GET /rest/api/3/search (returns 410 Gone) in favor of
        # the enhanced JQL search endpoint below — same params, same response shape.
        r = requests.get(f"{base}/search/jql", headers=_jira_headers(), params=params, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  [loader] Jira API error ({e}) — falling back to synthetic data")
        return json.loads((SYNTHETIC_DATA_PATH / "jira_tickets.json").read_text())

    tickets = []
    for issue in r.json().get("issues", []):
        f = issue["fields"]

        desc_raw = f.get("description") or {}
        desc = _adf_to_text(desc_raw) if isinstance(desc_raw, dict) else str(desc_raw or "")
        if not desc.strip():
            continue  # skip Jira's auto-generated sample tickets (no description)

        comments = []
        for c in (f.get("comment") or {}).get("comments", []):
            body_raw = c.get("body") or {}
            body = _adf_to_text(body_raw) if isinstance(body_raw, dict) else str(body_raw or "")
            # Strip the "[Author]: " prefix we added during populate
            if body.startswith("[") and "]: " in body:
                author_part, body = body.split("]: ", 1)
                author = author_part.lstrip("[")
            else:
                author = (c.get("author") or {}).get("displayName", "")
            comments.append({
                "author":     author,
                "body":       body,
                "created_at": c.get("created", ""),
            })

        tickets.append({
            "external_id": issue["key"],
            "title":       f.get("summary", ""),
            "description": desc,
            "status":      (f.get("status") or {}).get("name", ""),
            "author":      (f.get("reporter") or {}).get("displayName", ""),
            "assignee":    (f.get("assignee") or {}).get("displayName", ""),
            "created_at":  f.get("created", ""),
            "updated_at":  f.get("updated", ""),
            "url":         f"https://{JIRA_DOMAIN}.atlassian.net/browse/{issue['key']}",
            "comments":    comments,
        })

    print(f"  [loader] Jira: fetched {len(tickets)} issues from {JIRA_DOMAIN}.atlassian.net")
    return tickets


# ══════════════════════════════════════════════════════════════════════════════
# SLACK
# ══════════════════════════════════════════════════════════════════════════════

_SLACK_SYSTEM_SUBTYPES = {
    "channel_join", "channel_leave", "channel_topic", "channel_purpose",
    "channel_name", "channel_archive", "channel_unarchive",
    "pinned_item", "unpinned_item",
}


def load_slack(force_synthetic: bool = False) -> list[dict]:
    if force_synthetic or not SLACK_BOT_TOKEN:
        print("  [loader] Slack: using synthetic data" if force_synthetic else
              "  [loader] Slack: credentials not set — using synthetic data")
        return json.loads((SYNTHETIC_DATA_PATH / "slack_threads.json").read_text())

    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}

    # Fetch all channels
    try:
        r = requests.get(
            "https://slack.com/api/conversations.list",
            headers=headers,
            params={"types": "public_channel", "limit": 200},
            timeout=15,
        )
        data = r.json()
        if not data.get("ok"):
            raise ValueError(data.get("error", "unknown"))
        channels = {c["name"]: c["id"] for c in data.get("channels", [])}
    except Exception as e:
        print(f"  [loader] Slack API error ({e}) — falling back to synthetic data")
        return json.loads((SYNTHETIC_DATA_PATH / "slack_threads.json").read_text())

    # Cache user display names
    user_cache: dict = {}

    def get_username(user_id: str) -> str:
        if not user_id or user_id == "unknown":
            return "Unknown"
        if user_id not in user_cache:
            try:
                r2 = requests.get(
                    "https://slack.com/api/users.info",
                    headers=headers,
                    params={"user": user_id},
                    timeout=10,
                )
                profile = r2.json().get("user", {}).get("profile", {})
                user_cache[user_id] = (
                    profile.get("display_name")
                    or profile.get("real_name")
                    or user_id
                )
            except Exception:
                user_cache[user_id] = user_id
        return user_cache[user_id]

    target_channels = ["product-roadmap", "pricing-strategy", "engineering", "product-eng-sync"]
    threads = []

    for channel_name in target_channels:
        channel_id = channels.get(channel_name)
        if not channel_id:
            print(f"  [loader] Slack: channel '#{channel_name}' not found — skipping")
            continue

        try:
            r = requests.get(
                "https://slack.com/api/conversations.history",
                headers=headers,
                params={"channel": channel_id, "limit": 100},
                timeout=15,
            )
            history = r.json()
            if not history.get("ok"):
                print(f"  [loader] Slack: cannot read #{channel_name} ({history.get('error')})")
                continue
        except Exception as e:
            print(f"  [loader] Slack #{channel_name} error: {e}")
            continue

        for msg in history.get("messages", []):
            # Our own content arrives as subtype "bot_message" (posted via the
            # bot's chat.postMessage) — only skip actual system-event subtypes.
            if msg.get("subtype") in _SLACK_SYSTEM_SUBTYPES:
                continue

            text = msg.get("text", "")
            # Strip "*Author:* " prefix added during populate (fallback format)
            if text.startswith("*") and ":* " in text:
                parts = text.split(":* ", 1)
                author = parts[0].lstrip("*")
                text = parts[1]
            elif msg.get("username"):
                # chat:write.customize sets a per-message "username" override
                # directly on bot_message events — no "user" field present.
                author = msg["username"]
            else:
                author = get_username(msg.get("user", ""))

            thread_messages = [{"author": author, "text": text, "ts": msg.get("ts", "")}]

            # Fetch replies
            if msg.get("reply_count", 0) > 0:
                try:
                    r_replies = requests.get(
                        "https://slack.com/api/conversations.replies",
                        headers=headers,
                        params={"channel": channel_id, "ts": msg["ts"]},
                        timeout=15,
                    )
                    for reply in r_replies.json().get("messages", [])[1:]:
                        reply_text = reply.get("text", "")
                        if reply_text.startswith("*") and ":* " in reply_text:
                            parts = reply_text.split(":* ", 1)
                            reply_author = parts[0].lstrip("*")
                            reply_text = parts[1]
                        elif reply.get("username"):
                            reply_author = reply["username"]
                        else:
                            reply_author = get_username(reply.get("user", ""))
                        thread_messages.append({
                            "author": reply_author,
                            "text":   reply_text,
                            "ts":     reply.get("ts", ""),
                        })
                except Exception:
                    pass

            ts = msg.get("ts", "")
            threads.append({
                "external_id": f"{channel_id}_{ts}",
                "channel":    channel_name,
                "channel_id": channel_id,
                "thread_ts":  ts,
                "messages":   thread_messages,
                "created_at": ts,
                "url": f"https://slack.com/archives/{channel_id}/p{ts.replace('.', '')}",
            })

    print(f"  [loader] Slack: fetched {len(threads)} threads across {len(target_channels)} channels")
    return threads


# ══════════════════════════════════════════════════════════════════════════════
# NOTION
# ══════════════════════════════════════════════════════════════════════════════

def load_notion(force_synthetic: bool = False) -> list[dict]:
    if force_synthetic or not NOTION_TOKEN:
        print("  [loader] Notion: using synthetic data" if force_synthetic else
              "  [loader] Notion: credentials not set — using synthetic data")
        return json.loads((SYNTHETIC_DATA_PATH / "notion_pages.json").read_text())

    headers = {
        "Authorization":  f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type":   "application/json",
    }

    def get_page_title(page: dict) -> str:
        for prop in page.get("properties", {}).values():
            if prop.get("type") == "title":
                return "".join(t.get("plain_text", "") for t in prop.get("title", []))
        return ""

    def blocks_to_text(page_id: str) -> str:
        try:
            r = requests.get(
                f"https://api.notion.com/v1/blocks/{page_id}/children",
                headers=headers,
                params={"page_size": 100},
                timeout=15,
            )
            blocks = r.json().get("results", [])
        except Exception:
            return ""

        lines = []
        for block in blocks:
            btype = block.get("type", "")
            if btype == "divider":
                # Marks a document boundary in multi-doc pages (e.g. a
                # markdown import of several notes into one page) — chunker
                # splits on this so chunks never straddle two documents.
                lines.append(DOC_BOUNDARY_MARKER)
                continue
            data  = block.get(btype, {})
            rich  = data.get("rich_text", [])
            text  = "".join(rt.get("plain_text", "") for rt in rich)
            if not text:
                continue
            if btype == "heading_1":
                lines.append(f"# {text}")
            elif btype == "heading_2":
                lines.append(f"## {text}")
            elif btype == "heading_3":
                lines.append(f"### {text}")
            elif btype == "bulleted_list_item":
                lines.append(f"• {text}")
            elif btype == "numbered_list_item":
                lines.append(f"- {text}")
            else:
                lines.append(text)
        return "\n".join(lines)

    def discover_child_pages(block_id: str, depth: int = 0, max_depth: int = 5) -> list[str]:
        """Recursively find child_page blocks nested under block_id (e.g. a
        markdown import that lands content under a 'notion_import' sub-page
        rather than directly on the page it was imported into)."""
        if depth > max_depth:
            return []
        try:
            r = requests.get(
                f"https://api.notion.com/v1/blocks/{block_id}/children",
                headers=headers,
                params={"page_size": 100},
                timeout=15,
            )
            children = r.json().get("results", [])
        except Exception:
            return []
        found = []
        for b in children:
            if b.get("type") == "child_page":
                found.append(b["id"])
                found.extend(discover_child_pages(b["id"], depth + 1, max_depth))
        return found

    # Two datasets, kept in one index but tagged separately:
    #   finlo_synthetic — child pages directly under NOTION_PARENT_PAGE_ID
    #     ("Finlo Knowledge Base"), the course's fictional-company data
    #   real_personal   — everything else the integration can see (e.g. a
    #     workspace-root page like "My Real Notes (v2 eval)"), found via
    #     /search and expanded recursively since markdown imports nest
    #     content under an auto-created child page
    page_ids_with_dataset: list[tuple] = []
    try:
        finlo_page_ids = []
        if NOTION_PARENT_PAGE_ID:
            r = requests.get(
                f"https://api.notion.com/v1/blocks/{NOTION_PARENT_PAGE_ID}/children",
                headers=headers,
                params={"page_size": 100},
                timeout=15,
            )
            raw = r.json().get("results", [])
            finlo_page_ids = [b["id"] for b in raw if b.get("type") == "child_page"]
        page_ids_with_dataset.extend((pid, "finlo_synthetic") for pid in finlo_page_ids)

        r2 = requests.post(
            "https://api.notion.com/v1/search",
            headers=headers,
            json={"filter": {"property": "object", "value": "page"}, "page_size": 100},
            timeout=15,
        )
        all_pages = [p for p in r2.json().get("results", []) if p.get("object") == "page"]
        # Notion API ids are hyphenated UUIDs; .env's NOTION_PARENT_PAGE_ID is
        # stored unhyphenated — normalize before comparing or the parent page
        # itself leaks through as "real_personal".
        norm = lambda x: x.replace("-", "")
        excluded = {norm(pid) for pid in finlo_page_ids}
        if NOTION_PARENT_PAGE_ID:
            excluded.add(norm(NOTION_PARENT_PAGE_ID))
        for p in all_pages:
            pid = p["id"]
            if norm(pid) in excluded:
                continue
            page_ids_with_dataset.append((pid, "real_personal"))
            page_ids_with_dataset.extend(
                (cid, "real_personal") for cid in discover_child_pages(pid)
            )

        page_objects = []
        seen = set()
        for pid, dataset in page_ids_with_dataset:
            if pid in seen:
                continue
            seen.add(pid)
            pr = requests.get(f"https://api.notion.com/v1/pages/{pid}", headers=headers, timeout=10)
            if pr.status_code == 200:
                page = pr.json()
                page["_dataset"] = dataset
                page_objects.append(page)
    except Exception as e:
        print(f"  [loader] Notion API error ({e}) — falling back to synthetic data")
        return json.loads((SYNTHETIC_DATA_PATH / "notion_pages.json").read_text())

    pages = []
    for page in page_objects:
        title = get_page_title(page)
        if not title:
            continue
        page_id = page["id"]
        content = blocks_to_text(page_id)

        # Strip the "[meta] author=...; created=..." marker line (added by
        # populate_notion.py) and use it to recover the real narrative author/
        # date — Notion's own created_time only reflects the API call time.
        author = ""
        created_at = page.get("created_time", "")
        lines = content.split("\n")
        if lines and lines[0].startswith("[meta] "):
            for kv in lines[0][len("[meta] "):].split(";"):
                k, _, v = kv.strip().partition("=")
                if k == "author":
                    author = v
                elif k == "created":
                    created_at = v
            content = "\n".join(lines[1:]).lstrip("\n")

        pages.append({
            "external_id": page_id,
            "title":       title,
            "content":     content,
            "author":      author,
            "created_at":  created_at,
            "updated_at":  page.get("last_edited_time", ""),
            "url":         page.get("url", f"https://notion.so/{page_id.replace('-', '')}"),
            "dataset":     page.get("_dataset", "finlo_synthetic"),
        })

    print(f"  [loader] Notion: fetched {len(pages)} pages")
    return pages
