from sentence_transformers import SentenceTransformer
from contextpm.config import EMBEDDING_MODEL

_model = SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    return _model.encode(texts, show_progress_bar=False).tolist()
