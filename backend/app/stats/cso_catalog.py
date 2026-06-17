import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.stats.cso_client import fetch_collection

logger = logging.getLogger(__name__)

CATALOG_FILE = "cso_catalog.json"


def _catalog_path(cache_dir: Path) -> Path:
    return cache_dir / CATALOG_FILE


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


def search_catalog(query: str, cache_dir: Path, top_k: int = 5, catalog=None) -> list[dict]:
    if catalog is None:
        catalog = build_catalog(cache_dir)
    if not catalog:
        return []

    kw = [w for w in query.lower().split() if len(w) > 2]
    scored = []
    for entry in catalog:
        title_lower = entry["title"].lower()
        score = sum(1 for k in kw if k in title_lower)
        if score > 0:
            scored.append((score, entry))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in scored[:top_k]]


# TODO: add more topics as the project grows
_TOPIC_HINTS: dict[str, list[str]] = {
    "inflation": ["CPM01", "CPM03"],
    "consumer price": ["CPM01", "CPM03"],
    "cpi": ["CPM01", "CPM03"],
    "house completions": ["URA26", "NDQ01"],
    "housing completions": ["URA26", "NDQ01"],
    "dwelling": ["URA26", "NDQ01"],
    "housing": ["URA26", "HPM09"],
    "unemployment": ["LRM09", "MIP11"],
    "employment": ["LRM09", "LRQ02"],
    "labour force": ["LRM09", "LRQ02"],
    "gdp": ["NA001", "EAA01"],
    "earnings": ["EHQ01", "EHA01"],
    "rent": ["HPM09", "RIQ01"],
    "rents": ["HPM09", "RIQ01"],
    "house prices": ["HPM09", "HPQ01"],
    "immigration": ["PEA14", "PEA15"],
    "asylum": ["PEA14", "PEA15"],
    "population": ["PEA01", "PEA14"],
    "homelessness": ["HOM01", "SHA07"],
    "homeless": ["HOM01", "SHA07"],
    "emissions": ["EAA07", "GHG01"],
    "climate": ["EAA07", "GHG01"],
    "hospital": ["HEA10", "HEA11"],
    "waiting list": ["HEA10", "HEA11"],
    "health spending": ["GFS01", "HEA15"],
    "education spending": ["GFS01", "EDA07"],
    "school": ["EDA07", "EDA01"],
    "social housing": ["URA26", "SHA07"],
    "tourism": ["ITA07", "TMQ05"],
    "visitor numbers": ["ITA07"],
    "tourists": ["ITA07", "TMQ05"],
    "overnight visitors": ["ITA07"],
}


def get_best_matrix(query: str, cache_dir: Path) -> str | None:
    ql = query.lower()
    for kw, matrices in _TOPIC_HINTS.items():
        if kw in ql:
            return matrices[0]
    results = search_catalog(query, cache_dir, top_k=1)
    return results[0]["matrix"] if results else None
