import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent

# Streamlit Community Cloud mounts the repo at /mount/src/<repo> — a stable
# signature of that specific hosting environment. Used to hide things that
# only make sense for the app owner running locally with real account
# access (e.g. "Open in Notion/Jira" links that would be a dead end for a
# public visitor), independent of whatever credentials happen to be
# configured in st.secrets.
IS_STREAMLIT_CLOUD = Path("/mount/src").exists()


def _get(key: str, default: str = "") -> str:
    """Read a config value from the OS environment (populated locally by
    load_dotenv() from .env), falling back to Streamlit Cloud's st.secrets.
    Streamlit Cloud's Secrets manager injects values into st.secrets, not
    os.environ, so without this fallback the app would see them as unset
    when deployed there."""
    val = os.environ.get(key)
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


def _require(key: str) -> str:
    val = _get(key)
    if not val:
        raise RuntimeError(
            f"{key} is not set — add it to .env locally or to Streamlit "
            "Cloud's Secrets manager."
        )
    return val


OPENAI_API_KEY = _get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")

SQLITE_PATH = ROOT / "contextpm.db"
CHROMA_PATH = ROOT / "chroma_db"
SYNTHETIC_DATA_PATH = ROOT / "data" / "synthetic"

# Local embeddings via sentence-transformers (all-MiniLM-L6-v2, 384-dim)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "claude-haiku-4-5-20251001"
TOP_K_CHUNKS = 8
LOW_CONFIDENCE_THRESHOLD = 0.35  # all-MiniLM-L6-v2 cosine scores cluster 0.44-0.69; 0.5 was calibrated for OpenAI embeddings

# ── Real tool API credentials (.env locally, st.secrets on Streamlit Cloud) ──
# Jira Cloud
JIRA_DOMAIN    = _get("JIRA_DOMAIN")       # e.g. "finlo" → finlo.atlassian.net
JIRA_EMAIL     = _get("JIRA_EMAIL")
JIRA_API_TOKEN = _get("JIRA_API_TOKEN")
JIRA_PROJECT   = _get("JIRA_PROJECT", "FINLO")

# Slack
SLACK_BOT_TOKEN = _get("SLACK_BOT_TOKEN")  # xoxb-...

# Notion
NOTION_TOKEN          = _get("NOTION_TOKEN")           # ntn_...
NOTION_PARENT_PAGE_ID = _get("NOTION_PARENT_PAGE_ID")
