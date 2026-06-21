"""
SQLite schema — creates all 7 tables from the Phase 2 data model.
Run once: python -m contextpm.db.schema
"""
import sqlite3
from contextpm.config import SQLITE_PATH


DDL = """
CREATE TABLE IF NOT EXISTS user (
    id              TEXT PRIMARY KEY,
    email           TEXT UNIQUE NOT NULL,
    name            TEXT NOT NULL,
    password_hash   TEXT,
    created_at      TEXT NOT NULL,
    connected_tools TEXT NOT NULL DEFAULT '[]',
    settings        TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS ingestion_job (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES user(id),
    tool_type       TEXT NOT NULL CHECK (tool_type IN ('jira','slack','notion')),
    status          TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending','running','completed','failed')),
    started_at      TEXT,
    completed_at    TEXT,
    source_count    INTEGER NOT NULL DEFAULT 0,
    chunk_count     INTEGER NOT NULL DEFAULT 0,
    error_message   TEXT
);

CREATE TABLE IF NOT EXISTS source (
    id                  TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL REFERENCES user(id),
    tool_type           TEXT NOT NULL CHECK (tool_type IN ('jira','slack','notion')),
    external_id         TEXT NOT NULL,
    url                 TEXT NOT NULL,
    title               TEXT NOT NULL,
    raw_content         TEXT NOT NULL,
    author              TEXT,
    created_at_source   TEXT,
    updated_at_source   TEXT,
    ingestion_job_id    TEXT NOT NULL REFERENCES ingestion_job(id),
    metadata            TEXT NOT NULL DEFAULT '{}',
    UNIQUE (user_id, tool_type, external_id)
);

CREATE TABLE IF NOT EXISTS chunk (
    id          TEXT PRIMARY KEY,
    source_id   TEXT NOT NULL REFERENCES source(id),
    content     TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    token_count INTEGER NOT NULL,
    metadata    TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS query (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES user(id),
    query_text  TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS answer (
    id                  TEXT PRIMARY KEY,
    query_id            TEXT NOT NULL REFERENCES query(id),
    answer_text         TEXT NOT NULL,
    cited_chunk_ids     TEXT NOT NULL DEFAULT '[]',
    cited_source_ids    TEXT NOT NULL DEFAULT '[]',
    tool_types_cited    TEXT NOT NULL DEFAULT '[]',
    latency_ms          INTEGER,
    model_used          TEXT,
    prompt_tokens       INTEGER,
    completion_tokens   INTEGER,
    confidence_score    REAL,
    result_status       TEXT NOT NULL DEFAULT 'answered'
                            CHECK (result_status IN ('answered','low_confidence','no_results')),
    created_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    id          TEXT PRIMARY KEY,
    answer_id   TEXT NOT NULL REFERENCES answer(id),
    user_id     TEXT REFERENCES user(id),
    rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    helpful     INTEGER NOT NULL DEFAULT 0,
    comment     TEXT,
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_source_user       ON source(user_id);
CREATE INDEX IF NOT EXISTS idx_chunk_source      ON chunk(source_id);
CREATE INDEX IF NOT EXISTS idx_query_user        ON query(user_id);
CREATE INDEX IF NOT EXISTS idx_answer_query      ON answer(query_id);
CREATE INDEX IF NOT EXISTS idx_feedback_answer   ON feedback(answer_id);
"""


def init_db(path=None):
    db_path = path or SQLITE_PATH
    conn = sqlite3.connect(db_path)
    conn.executescript(DDL)
    conn.commit()
    conn.close()
    return db_path


def get_conn(path=None):
    db_path = path or SQLITE_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


if __name__ == "__main__":
    path = init_db()
    conn = sqlite3.connect(path)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    conn.close()
    print(f"Database: {path}")
    print(f"Tables created: {[t[0] for t in tables]}")
