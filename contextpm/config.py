import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

SQLITE_PATH = ROOT / "contextpm.db"
CHROMA_PATH = ROOT / "chroma_db"
SYNTHETIC_DATA_PATH = ROOT / "data" / "synthetic"

# Local embeddings via sentence-transformers (all-MiniLM-L6-v2, 384-dim)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "claude-haiku-4-5-20251001"
TOP_K_CHUNKS = 8
LOW_CONFIDENCE_THRESHOLD = 0.35  # all-MiniLM-L6-v2 cosine scores cluster 0.44-0.69; 0.5 was calibrated for OpenAI embeddings

# ── Real tool API credentials (set in .env) ──────────────────────────────────
# Jira Cloud
JIRA_DOMAIN    = os.environ.get("JIRA_DOMAIN", "")       # e.g. "finlo" → finlo.atlassian.net
JIRA_EMAIL     = os.environ.get("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
JIRA_PROJECT   = os.environ.get("JIRA_PROJECT", "FINLO")

# Slack
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")  # xoxb-...

# Notion
NOTION_TOKEN          = os.environ.get("NOTION_TOKEN", "")           # ntn_...
NOTION_PARENT_PAGE_ID = os.environ.get("NOTION_PARENT_PAGE_ID", "")
