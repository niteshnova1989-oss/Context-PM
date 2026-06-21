"""
Embeds the query and retrieves the top-K most similar chunks from ChromaDB.
Returns enriched results with source metadata from SQLite.
"""
import chromadb

from contextpm.config import CHROMA_PATH, TOP_K_CHUNKS
from contextpm.db.schema import get_conn
from contextpm.ingestion.embedder import embed_texts


def retrieve(query_text: str, top_k: int = TOP_K_CHUNKS) -> list[dict]:
    """
    Returns a list of dicts, best match first:
      chunk_id, content, score (0-1), source_id,
      tool_type, title, url, author, created_at_source
    """
    query_embedding = embed_texts([query_text])[0]

    chroma = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = chroma.get_or_create_collection(
        name="contextpm_chunks",
        metadata={"hnsw:space": "cosine"},
    )

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for chunk_id, content, meta, distance in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        # cosine distance → similarity: score = 1 - distance
        score = round(1.0 - distance, 4)
        chunks.append({
            "chunk_id":          chunk_id,
            "content":           content,
            "score":             score,
            "source_id":         meta.get("source_id", ""),
            "tool_type":         meta.get("tool_type", ""),
            "title":             meta.get("title", ""),
            "url":               meta.get("url", ""),
            "author":            meta.get("author", ""),
            "created_at_source": meta.get("created_at_source", ""),
            "dataset":           meta.get("dataset", "finlo_synthetic"),
        })

    return chunks
