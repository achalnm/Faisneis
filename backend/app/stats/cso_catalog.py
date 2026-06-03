import json
import logging
import re
from pathlib import Path
from typing import Optional

from app.stats.cso_client import fetch_collection
from app.retrieval.embeddings import embed, embed_one

logger = logging.getLogger(__name__)

CATALOG_FILE = "cso_catalog.json"
TITLE_EMBEDDINGS_FILE = "cso_title_embeddings.json"


def _catalog_path(cache_dir: Path) -> Path:
    return cache_dir / CATALOG_FILE


def _embeddings_path(cache_dir: Path) -> Path:
    return cache_dir / TITLE_EMBEDDINGS_FILE


def build_catalog(cache_dir: Path, force: bool = False) -> list[dict]:
    p = _catalog_path(cache_dir)
    if p.exists() and not force:
        return json.loads(p.read_bytes())

    logger.info("Building CSO catalog from ReadCollection...")
    toc = fetch_collection(cache_dir)
    items = toc.get("link", {}).get("item", [])
    logger.info("Found %d items in CSO collection", len(items))

    catalog = []
    seen = set()
    for item in items:
        ext = item.get("extension", {})
        matrix = ext.get("matrix", "")
        if not matrix or matrix in seen:
            continue
        seen.add(matrix)
        catalog.append({
            "matrix": matrix,
            "title": item.get("label", ""),
            "last_updated": ext.get("last-updated", ""),
        })

    p.write_bytes(json.dumps(catalog).encode())
    logger.info("Catalog built: %d unique tables", len(catalog))
    return catalog


def _load_or_build_embeddings(catalog: list[dict], cache_dir: Path) -> list[list[float]]:
    ep = _embeddings_path(cache_dir)
    if ep.exists():
        stored = json.loads(ep.read_bytes())
        if len(stored) == len(catalog):
            return stored

    logger.info("Embedding %d CSO table titles...", len(catalog))
    titles = [c["title"] for c in catalog]
    vecs = embed(titles)
    ep.write_bytes(json.dumps(vecs).encode())
    return vecs


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def search_catalog(
    query: str,
    cache_dir: Path,
    top_k: int = 5,
    catalog: Optional[list[dict]] = None,
) -> list[dict]:
    if catalog is None:
        catalog = build_catalog(cache_dir)

    if not catalog:
        return []

    kw = query.lower().split()

    ep = _embeddings_path(cache_dir)
    if ep.exists():
        title_vecs = _load_or_build_embeddings(catalog, cache_dir)
        q_vec = embed_one(query)
        scored = [
            (_cosine_sim(q_vec, tv), entry)
            for tv, entry in zip(title_vecs, catalog)
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [e for _, e in scored[:top_k]]
        best_score = scored[0][0] if scored else 0
        if best_score < 0.35:
            seen = {e["matrix"] for e in top}
            for e in catalog:
                if any(k in e["title"].lower() for k in kw) and e["matrix"] not in seen:
                    top.append(e)
                    seen.add(e["matrix"])
        return top[:top_k]

    return [e for e in catalog if any(k in e["title"].lower() for k in kw)][:top_k]


_TOPIC_HINTS: dict[str, list[str]] = {
    "inflation": ["CPM01", "CPM03"],
    "consumer price": ["CPM01", "CPM03"],
    "cpi": ["CPM01", "CPM03"],
    "house completions": ["URA26", "NDQ01"],
    "housing completions": ["URA26", "NDQ01"],
    "dwelling": ["URA26", "NDQ01"],
    "unemployment": ["LRM09", "MIP11"],
    "employment": ["LRM09", "LRQ02"],
    "labour force": ["LRM09", "LRQ02"],
    "gdp": ["NA001", "EAA01"],
    "earnings": ["EHQ01", "EHA01"],
    "rent": ["HPM09", "RIQ01"],
    "house prices": ["HPM09", "HPQ01"],
}


def get_best_matrix(query: str, cache_dir: Path) -> str | None:
    ql = query.lower()
    for kw, matrices in _TOPIC_HINTS.items():
        if kw in ql:
            return matrices[0]
    results = search_catalog(query, cache_dir, top_k=1)
    return results[0]["matrix"] if results else None
