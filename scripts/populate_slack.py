"""
Populates a real Slack workspace with the 10 synthetic Finlo threads.

Prerequisites:
  1. Create a free Slack workspace at https://slack.com/create
     Name it "Finlo" (or any name)
  2. Create 4 channels manually:
       #product-roadmap  #pricing-strategy  #engineering  #product-eng-sync
  3. Create a Slack App:
       a. Go to https://api.slack.com/apps → "Create New App" → "From scratch"
       b. Name: "ContextPM Bot"  |  Pick your Finlo workspace
       c. Go to "OAuth & Permissions" → "Bot Token Scopes" → Add:
            channels:history   channels:read   channels:write (or chat:write)
            chat:write.customize   users:read   groups:read   groups:history
       d. Click "Install to Workspace" → Copy the "Bot OAuth Token" (xoxb-...)
       e. Invite the bot to each channel: /invite @ContextPM Bot
  4. Set in .env:
       SLACK_BOT_TOKEN=xoxb-your-token-here

Run:
    .venv/bin/python scripts/populate_slack.py
"""
import sys, json, time
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import os, requests

TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
if not TOKEN:
    print("ERROR: Set SLACK_BOT_TOKEN in .env")
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
THREADS = json.loads((ROOT / "data" / "synthetic" / "slack_threads.json").read_text())


def get_channels() -> dict:
    r = requests.get(
        "https://slack.com/api/conversations.list",
        headers=HEADERS,
        params={"types": "public_channel", "limit": 200},
    )
    data = r.json()
    if not data.get("ok"):
        print(f"ERROR listing channels: {data.get('error')}")
        return {}
    return {c["name"]: c["id"] for c in data.get("channels", [])}


def post_message(channel_id: str, author: str, text: str) -> Optional[str]:
    payload = {
        "channel":  channel_id,
        "text":     text,
        "username": author,
        "icon_emoji": ":bust_in_silhouette:",
    }
    r = requests.post("https://slack.com/api/chat.postMessage", headers=HEADERS, json=payload)
    data = r.json()
    if not data.get("ok"):
        print(f"      ✗ Failed: {data.get('error')}  (may need chat:write.customize scope)")
        # Fallback: post with author name prepended to text
        payload2 = {"channel": channel_id, "text": f"*{author}:* {text}"}
        r2 = requests.post("https://slack.com/api/chat.postMessage", headers=HEADERS, json=payload2)
        data2 = r2.json()
        if data2.get("ok"):
            return data2["ts"]
        print(f"      ✗ Fallback also failed: {data2.get('error')}")
        return None
    return data["ts"]


def post_reply(channel_id: str, thread_ts: str, author: str, text: str):
    payload = {
        "channel":   channel_id,
        "thread_ts": thread_ts,
        "text":      text,
        "username":  author,
        "icon_emoji": ":bust_in_silhouette:",
    }
    r = requests.post("https://slack.com/api/chat.postMessage", headers=HEADERS, json=payload)
    data = r.json()
    if not data.get("ok"):
        payload2 = {"channel": channel_id, "thread_ts": thread_ts, "text": f"*{author}:* {text}"}
        requests.post("https://slack.com/api/chat.postMessage", headers=HEADERS, json=payload2)


if __name__ == "__main__":
    print("\nPopulating Slack workspace with Finlo threads\n")
    channels = get_channels()
    if not channels:
        print("Could not fetch channels. Check your SLACK_BOT_TOKEN.")
        sys.exit(1)

    posted = 0
    for thread in THREADS:
        # channel name in data has '#' prefix — strip it
        channel_name = thread["channel"].lstrip("#")
        channel_id = channels.get(channel_name)
        if not channel_id:
            print(f"  ✗  Channel '#{channel_name}' not found — create it and invite the bot")
            continue

        messages = thread["messages"]
        if not messages:
            continue

        print(f"  #{channel_name}  ({len(messages)} messages)")
        first = messages[0]
        thread_ts = post_message(channel_id, first["author"], first["text"])
        if thread_ts:
            print(f"      ✓ [{first['author']}] {first['text'][:60]}…")
            posted += 1
            for msg in messages[1:]:
                time.sleep(1)  # rate limit: 1 msg/sec on free plan
                post_reply(channel_id, thread_ts, msg["author"], msg["text"])
                print(f"      ✓ [{msg['author']}] {msg['text'][:60]}…")

    print(f"\nDone. {posted}/{len(THREADS)} threads posted.\n")
