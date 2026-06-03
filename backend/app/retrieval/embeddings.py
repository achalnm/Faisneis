"""
Thin wrapper around sentence-transformers. Loads the model once and keeps
it in memory. The model name comes from config so it can be swapped without
touching any other code.
"""

from functools import lru_cache
from sentence_transformers import SentenceTransformer
from app.config import settings


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(settings.embed_model)


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return _model().encode(texts, convert_to_numpy=True).tolist()


def embed_one(text: str) -> list[float]:
    return embed([text])[0]
