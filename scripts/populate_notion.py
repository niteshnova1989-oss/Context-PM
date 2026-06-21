"""
Populates a real Notion workspace with the 8 synthetic Finlo pages.

Prerequisites:
  1. Create a free Notion account at https://www.notion.so
  2. Create a top-level page named "Finlo Knowledge Base" (this will hold all 8 pages)
  3. Create a Notion integration:
       a. Go to https://www.notion.so/my-integrations
       b. Click "+ New integration"
       c. Name: "ContextPM"  |  Associated workspace: your workspace
       d. Capabilities: Read content, Update content, Insert content
       e. Copy the "Internal Integration Secret" (ntn_... or secret_...)
  4. Share the "Finlo Knowledge Base" page with the integration:
       a. Open the page → click "..." top-right → "Connections" → "ContextPM"
  5. Copy the page ID from the URL:
       notion.so/{workspace}/{PAGE_ID}?v=...
       It's the 32-char hex string after the last slash, before "?v"
  6. Set in .env:
       NOTION_TOKEN=ntn_your_integration_secret
       NOTION_PARENT_PAGE_ID=your_32char_page_id (with or without dashes)

Run:
    .venv/bin/python scripts/populate_notion.py
"""
import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import os, requests

TOKEN     = os.environ.get("NOTION_TOKEN", "")
PARENT_ID = os.environ.get("NOTION_PARENT_PAGE_ID", "").replace("-", "")

if not TOKEN or not PARENT_ID:
    print("ERROR: Set NOTION_TOKEN and NOTION_PARENT_PAGE_ID in .env")
    sys.exit(1)

HEADERS = {
    "Authorization":  f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type":   "application/json",
}

PAGES = json.loads((ROOT / "data" / "synthetic" / "notion_pages.json").read_text())
CHUNK_SIZE = 95  # Notion max blocks per request


def content_to_blocks(content: str) -> list:
    blocks = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Trim to 2000 chars (Notion rich_text limit)
        stripped = stripped[:2000]
        if stripped.startswith("### "):
            blocks.append({"object": "block", "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": stripped[4:]}}]}})
        elif stripped.startswith("## "):
            blocks.append({"object": "block", "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": stripped[3:]}}]}})
        elif stripped.startswith("# "):
            blocks.append({"object": "block", "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": stripped[2:]}}]}})
        else:
            blocks.append({"object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": stripped}}]}})
    return blocks


def page_exists(title: str) -> bool:
    r = requests.post(
        "https://api.notion.com/v1/search",
        headers=HEADERS,
        json={"query": title, "filter": {"property": "object", "value": "page"}},
    )
    for result in r.json().get("results", []):
        props = result.get("properties", {})
        for prop in props.values():
            if prop.get("type") == "title":
                existing = "".join(t.get("plain_text", "") for t in prop.get("title", []))
                if existing.strip() == title.strip():
                    return True
    return False


def create_page(page: dict) -> str:
    title = page["title"]
    if page_exists(title):
        print(f"  ↩  Already exists: '{title}'")
        return ""

    # Notion's API has no "author"/"created_at" override — page metadata always
    # reflects the live API call, not the narrative date. Embed it as a parseable
    # marker block instead, mirroring the [Author]: prefix pattern used for Jira/
    # Slack. loader.py strips this back out and restores the real author/date.
    meta_line = f"[meta] author={page['author']}; created={page['created_at']}"
    meta_block = {"object": "block", "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": meta_line}}]}}

    all_blocks = [meta_block] + content_to_blocks(page["content"])
    # Create page with first batch of blocks (max 100 on create)
    first_batch = all_blocks[:CHUNK_SIZE]
    payload = {
        "parent": {"page_id": PARENT_ID},
        "properties": {
            "title": {"title": [{"text": {"content": title}}]}
        },
        "children": first_batch,
    }
    r = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
    if r.status_code not in (200, 201):
        print(f"  ✗  Failed '{title}': {r.text[:200]}")
        return ""

    page_id = r.json()["id"]
    print(f"  ✓  Created: '{title}'  ({page_id})")

    # Append remaining blocks in chunks
    remaining = all_blocks[CHUNK_SIZE:]
    while remaining:
        batch = remaining[:CHUNK_SIZE]
        remaining = remaining[CHUNK_SIZE:]
        r2 = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=HEADERS,
            json={"children": batch},
        )
        if r2.status_code not in (200, 201):
            print(f"      ✗ Append failed: {r2.text[:100]}")

    return page_id


if __name__ == "__main__":
    print(f"\nPopulating Notion workspace (parent page: {PARENT_ID})\n")
    created = 0
    for page in PAGES:
        pid = create_page(page)
        if pid:
            created += 1
    print(f"\nDone. {created} new pages created under 'Finlo Knowledge Base'.\n")
    print("IMPORTANT: If you see 'Already exists' for all pages, they were already created.")
    print("View at https://www.notion.so\n")
