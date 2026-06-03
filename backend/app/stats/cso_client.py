import hashlib
import json
import logging
import time
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

CSO_BASE = "https://ws.cso.ie/public/api.restful"
REQUEST_DELAY = 0.5


def _cache_path(cache_dir: Path, url: str) -> Path:
    key = hashlib.sha256(url.encode()).hexdigest()[:16]
    return cache_dir / f"cso_{key}.json"


def _load_cached(cache_dir: Path, url: str) -> dict | None:
    p = _cache_path(cache_dir, url)
    if p.exists():
        return json.loads(p.read_bytes())
    return None


def _save_cache(cache_dir: Path, url: str, data: dict) -> None:
    p = _cache_path(cache_dir, url)
    p.write_bytes(json.dumps(data).encode())


def _get_json(client: httpx.Client, url: str, cache_dir: Path) -> dict:
    cached = _load_cached(cache_dir, url)
    if cached is not None:
        return cached

    delays = [0, 1, 2, 4, 8]
    last_exc: Exception | None = None
    for delay in delays:
        if delay:
            time.sleep(delay)
        else:
            time.sleep(REQUEST_DELAY)
        try:
            r = client.get(url, timeout=60)
            r.raise_for_status()
            data = r.json()
            _save_cache(cache_dir, url, data)
            return data
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                raise
            last_exc = e
            logger.warning("HTTP %d on %s", e.response.status_code, url)
        except httpx.TransportError as e:
            last_exc = e
            logger.warning("Transport error on %s", url)

    raise RuntimeError(f"All retries failed for {url}") from last_exc


def fetch_collection(cache_dir: Path) -> dict:
    url = f"{CSO_BASE}/PxStat.Data.Cube_API.ReadCollection"
    with httpx.Client() as client:
        return _get_json(client, url, cache_dir)


def fetch_dataset(matrix: str, cache_dir: Path) -> dict:
    url = f"{CSO_BASE}/PxStat.Data.Cube_API.ReadDataset/{matrix}/JSON-stat/2.0/en"
    with httpx.Client() as client:
        return _get_json(client, url, cache_dir)


def dataset_source_url(matrix: str) -> str:
    return f"https://data.cso.ie/table/{matrix}"
