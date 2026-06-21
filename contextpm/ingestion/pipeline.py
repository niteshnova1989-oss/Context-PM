"""
Ingestion pipeline — orchestrates load → chunk → embed → store.
Run: python -m contextpm.ingestion.pipeline
"""
import json
import uuid
from datetime import datetime, timezone

import chromadb

from contextpm.config import CHROMA_PATH
from contextpm.db.schema import get_conn, get_or_create_default_user, init_db
from contextpm.ingestion.chunker import CHUNKERS
from contextpm.ingestion.embedder import embed_texts
from contextpm.ingestion.loader import load_jira, load_notion, load_slack

LOADERS = {
    "jira":   load_jira,
    "slack":  load_slack,
    "notion": load_notion,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _raw_content(tool_type: str, doc: dict) -> str:
    if tool_type == "jira":
        parts = [doc["description"]]
        for c in doc.get("comments", []):
            parts.append(c["body"])
        return "\n\n".join(parts)
    if tool_type == "slack":
        return "\n".join(f"{m['author']}: {m['text']}" for m in doc["messages"])
    return doc["content"]  # notion


def _source_meta(tool_type: str, doc: dict) -> dict:
    # Tag every doc with which dataset it belongs to, so eval results can be
    # filtered/compared by dataset later even though everything lives in one
    # Chroma collection / SQLite DB. Jira and Slack are Finlo-only today;
    # Notion docs carry their own dataset from the loader (finlo_synthetic
    # vs real_personal).
    dataset = doc.get("dataset", "finlo_synthetic")
    if tool_type == "jira":
        return {
            "external_id":       doc["external_id"],
            "title":             doc["title"],
            "url":               doc["url"],
            "author":            doc["author"],
            "created_at_source": doc["created_at"],
            "updated_at_source": doc["updated_at"],
            "dataset":           dataset,
        }
    if tool_type == "slack":
        first = doc["messages"][0]
        return {
            "external_id":       doc["external_id"],
            "title":             f"{doc['channel']} — {first['ts'][:10]}",
            "url":               doc["url"],
            "author":            first["author"],
            "created_at_source": first["ts"],
            "updated_at_source": doc["messages"][-1]["ts"],
            "dataset":           dataset,
        }
    return {
        "external_id":       doc["external_id"],
        "title":             doc["title"],
        "url":               doc["url"],
        "author":            doc["author"],
        "created_at_source": doc["created_at"],
        "updated_at_source": doc["updated_at"],
        "dataset":           dataset,
    }


def run_ingestion(force_synthetic: bool = False):
    """force_synthetic=True skips every tool's real-API branch regardless of
    whether credentials are configured — used for auto-bootstrapping the
    public Streamlit Cloud deployment so it always shows Finlo demo data,
    never real personal Jira/Slack/Notion content even if those credentials
    happen to be set in that environment."""
    init_db()
    conn = get_conn()
    user_id = get_or_create_default_user(conn)

    chroma = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = chroma.get_or_create_collection(
        name="contextpm_chunks",
        metadata={"hnsw:space": "cosine"},
    )

    total_sources = total_chunks = 0

    for tool_type, loader in LOADERS.items():
        chunker = CHUNKERS[tool_type]
        documents = loader(force_synthetic=force_synthetic)

        # Full refresh: each ingestion run replaces this tool's prior sources
        # outright, rather than merging by external_id. This is what lets
        # "Re-index now" actually rebuild the index, and avoids duplicate
        # source rows piling up whenever a tool's external_id scheme changes
        # (e.g. switching from synthetic fallback data to a real API).
        old_ids = [r["id"] for r in conn.execute(
            "SELECT id FROM source WHERE user_id=? AND tool_type=?",
            (user_id, tool_type),
        ).fetchall()]
        if old_ids:
            conn.executemany("DELETE FROM chunk WHERE source_id=?", [(sid,) for sid in old_ids])
            conn.executemany("DELETE FROM source WHERE id=?", [(sid,) for sid in old_ids])
            conn.commit()
        # Unconditional, not nested under `if old_ids:` — SQLite (contextpm.db)
        # and the Chroma vector store live at two independent paths on disk
        # and can fall out of sync (e.g. a Streamlit Cloud restart that resets
        # one but not the other). If that happens, old_ids being empty would
        # otherwise skip clearing Chroma, leaving stale vectors from a prior
        # run silently orphaned underneath the newly inserted ones.
        collection.delete(where={"tool_type": tool_type})

        job_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO ingestion_job (id, user_id, tool_type, status, started_at) "
            "VALUES (?,?,?,?,?)",
            (job_id, user_id, tool_type, "running", _now()),
        )
        conn.commit()

        job_sources = job_chunks = 0
        print(f"\n[{tool_type}] {len(documents)} documents")

        for doc in documents:
            meta = _source_meta(tool_type, doc)
            source_id = str(uuid.uuid4())

            conn.execute(
                """INSERT OR IGNORE INTO source
                   (id, user_id, tool_type, external_id, url, title, raw_content,
                    author, created_at_source, updated_at_source, ingestion_job_id, metadata)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    source_id, user_id, tool_type,
                    meta["external_id"], meta["url"], meta["title"],
                    _raw_content(tool_type, doc),
                    meta["author"], meta["created_at_source"],
                    meta["updated_at_source"], job_id,
                    json.dumps({"dataset": meta["dataset"]}),
                ),
            )
            conn.commit()

            # resolve actual id in case of IGNORE (duplicate)
            row = conn.execute(
                "SELECT id FROM source WHERE user_id=? AND tool_type=? AND external_id=?",
                (user_id, tool_type, meta["external_id"]),
            ).fetchone()
            source_id = row["id"]

            chunks = chunker(doc)
            embeddings = embed_texts([c["content"] for c in chunks])

            chroma_ids, chroma_embeddings, chroma_docs, chroma_metas = [], [], [], []
            for chunk, embedding in zip(chunks, embeddings):
                chunk_id = str(uuid.uuid4())
                chroma_ids.append(chunk_id)
                chroma_embeddings.append(embedding)
                chroma_docs.append(chunk["content"])
                chroma_metas.append({
                    "source_id":         source_id,
                    "tool_type":         tool_type,
                    "title":             meta["title"],
                    "url":               meta["url"],
                    "author":            meta["author"],
                    "created_at_source": meta["created_at_source"],
                    "dataset":           meta["dataset"],
                })
                chunk["metadata"]["dataset"] = meta["dataset"]
                conn.execute(
                    "INSERT INTO chunk (id, source_id, content, chunk_index, token_count, metadata) "
                    "VALUES (?,?,?,?,?,?)",
                    (chunk_id, source_id, chunk["content"],
                     chunk["chunk_index"], chunk["token_count"],
                     json.dumps(chunk["metadata"])),
                )

            if chroma_ids:
                collection.upsert(
                    ids=chroma_ids,
                    embeddings=chroma_embeddings,
                    documents=chroma_docs,
                    metadatas=chroma_metas,
                )
            conn.commit()

            job_sources += 1
            job_chunks += len(chunks)
            print(f"  ✓ {meta['external_id']:45s} {len(chunks)} chunk(s)")

        conn.execute(
            "UPDATE ingestion_job SET status='completed', completed_at=?, "
            "source_count=?, chunk_count=? WHERE id=?",
            (_now(), job_sources, job_chunks, job_id),
        )
        conn.commit()
        total_sources += job_sources
        total_chunks += job_chunks
        print(f"  [{tool_type}] {job_sources} sources, {job_chunks} chunks")

    conn.close()
    print(f"\nIngestion complete — {total_sources} sources, {total_chunks} chunks")
    print(f"ChromaDB collection size: {collection.count()}")
    return {"sources": total_sources, "chunks": total_chunks}


if __name__ == "__main__":
    run_ingestion()
