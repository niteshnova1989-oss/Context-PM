"""
Populates a real Jira Cloud project with the 10 synthetic Finlo tickets.

Prerequisites:
  1. Free Atlassian account at https://www.atlassian.com/try/cloud/signup?bundle=jira-software
  2. Create a Jira Software project — name "Finlo", key "FINLO"
  3. Get an API token at https://id.atlassian.com/manage-profile/security/api-tokens
  4. Set in .env:
       JIRA_DOMAIN=yoursite          (e.g. if URL is yoursite.atlassian.net)
       JIRA_EMAIL=you@example.com
       JIRA_API_TOKEN=your_token_here
       JIRA_PROJECT=FINLO

Run:
    .venv/bin/python scripts/populate_jira.py
"""
import sys, json, base64
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import os, requests

DOMAIN    = os.environ.get("JIRA_DOMAIN", "")
EMAIL     = os.environ.get("JIRA_EMAIL", "")
TOKEN     = os.environ.get("JIRA_API_TOKEN", "")
PROJECT   = os.environ.get("JIRA_PROJECT", "FINLO")

if not all([DOMAIN, EMAIL, TOKEN]):
    print("ERROR: Set JIRA_DOMAIN, JIRA_EMAIL, JIRA_API_TOKEN in .env")
    sys.exit(1)

BASE = f"https://{DOMAIN}.atlassian.net/rest/api/3"
AUTH = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
HEADERS = {"Authorization": f"Basic {AUTH}", "Content-Type": "application/json", "Accept": "application/json"}

TICKETS = json.loads((ROOT / "data" / "synthetic" / "jira_tickets.json").read_text())

STATUS_TO_TRANSITION = {
    "Done": "Done",
    "Cancelled": "Done",
    "In Progress": "In Progress",
    "Backlog": None,
}


def text_to_adf(text: str) -> dict:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        paragraphs = [""]
    return {
        "type": "doc", "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": p[:2000]}]}
            for p in paragraphs
        ],
    }


def get_transitions(issue_key: str) -> dict:
    r = requests.get(f"{BASE}/issue/{issue_key}/transitions", headers=HEADERS)
    return {t["name"]: t["id"] for t in r.json().get("transitions", [])}


def issue_exists(summary: str) -> Optional[str]:
    jql = f'project={PROJECT} AND summary~"{summary[:40]}"'
    r = requests.get(f"{BASE}/search", headers=HEADERS, params={"jql": jql, "maxResults": 1})
    issues = r.json().get("issues", [])
    return issues[0]["key"] if issues else None


def create_issue(ticket: dict) -> str:
    existing = issue_exists(ticket["title"])
    if existing:
        print(f"  ↩  Already exists: {existing}  ({ticket['title'][:50]})")
        return existing

    payload = {
        "fields": {
            "project":     {"key": PROJECT},
            "summary":     ticket["title"],
            "description": text_to_adf(ticket["description"]),
            "issuetype":   {"name": "Story"},
        }
    }
    r = requests.post(f"{BASE}/issue", headers=HEADERS, json=payload)
    if r.status_code not in (200, 201):
        print(f"  ✗  Failed to create '{ticket['title']}': {r.text[:200]}")
        return ""
    key = r.json()["key"]
    print(f"  ✓  Created {key}: {ticket['title'][:50]}")
    return key


def add_comment(issue_key: str, comment: dict):
    payload = {"body": text_to_adf(f"[{comment['author']}]: {comment['body']}")}
    r = requests.post(f"{BASE}/issue/{issue_key}/comment", headers=HEADERS, json=payload)
    if r.status_code not in (200, 201):
        print(f"      ✗ Comment failed: {r.text[:100]}")
    else:
        print(f"      ✓ Comment by {comment['author']}")


def transition_issue(issue_key: str, target_status: str):
    if not target_status or target_status == "Backlog":
        return
    transitions = get_transitions(issue_key)
    tid = transitions.get(target_status) or transitions.get("Done")
    if tid:
        requests.post(
            f"{BASE}/issue/{issue_key}/transitions",
            headers=HEADERS,
            json={"transition": {"id": tid}},
        )
        print(f"      → Status set to '{target_status}'")


if __name__ == "__main__":
    print(f"\nPopulating Jira project '{PROJECT}' at {DOMAIN}.atlassian.net\n")
    for ticket in TICKETS:
        key = create_issue(ticket)
        if key:
            for comment in ticket.get("comments", []):
                add_comment(key, comment)
            target = STATUS_TO_TRANSITION.get(ticket.get("status", ""), None)
            transition_issue(key, target)
    print(f"\nDone. View at https://{DOMAIN}.atlassian.net/jira/software/projects/{PROJECT}/boards\n")
