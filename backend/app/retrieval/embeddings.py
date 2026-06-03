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
    try:
        from fastembed import TextEmbedding
        return ("fastembed", TextEmbedding(model_name=_FASTEMBED_MODEL))
    except Exception:
        from sentence_transformers import SentenceTransformer
        return ("st", SentenceTransformer(settings.embed_model))


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    kind, model = _model()
    if kind == "fastembed":
        return [v.tolist() for v in model.embed(texts)]
    return model.encode(texts, convert_to_numpy=True).tolist()


def embed_one(text: str) -> list[float]:
    return embed([text])[0]
