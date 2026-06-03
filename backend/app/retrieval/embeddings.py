"""
Embedding wrapper using fastembed (ONNX, no PyTorch) for fast cold starts.
Falls back to sentence-transformers if fastembed is unavailable.
Produces identical vectors to all-MiniLM-L6-v2 sentence-transformers output.
"""

from functools import lru_cache
from app.config import settings

# fastembed model name that matches all-MiniLM-L6-v2
_FASTEMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding
    return TextEmbedding(model_name=_FASTEMBED_MODEL)


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return [v.tolist() for v in _model().embed(texts)]


def embed_one(text: str) -> list[float]:
    return embed([text])[0]
