import hashlib
import json
import time
import logging
from pathlib import Path
from typing import Iterator

import httpx

logger = logging.getLogger(__name__)

DEBATES_API = "https://api.oireachtas.ie/v1/debates"
PAGE_SIZE = 50
REQUEST_DELAY = 0.4


def _cache_path(cache_dir: Path, url: str, suffix: str = ".json") -> Path:
    key = hashlib.sha256(url.encode()).hexdigest()[:16]
    return cache_dir / f"{key}{suffix}"


def _get_cached(cache_dir: Path, url: str, suffix: str = ".json") -> bytes | None:
    p = _cache_path(cache_dir, url, suffix)
    if p.exists():
        return p.read_bytes()
    return None


def _put_cache(cache_dir: Path, url: str, data: bytes, suffix: str = ".json") -> None:
    p = _cache_path(cache_dir, url, suffix)
    p.write_bytes(data)


def _fetch_with_backoff(client: httpx.Client, url: str, **kwargs) -> httpx.Response:
    delays = [1, 2, 4, 8]
    last_exc: Exception | None = None
    for delay in [0] + delays:
        if delay:
            time.sleep(delay)
        try:
            r = client.get(url, **kwargs)
            r.raise_for_status()
            return r
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                raise
            last_exc = e
            logger.warning("HTTP %d on %s, retrying...", e.response.status_code, url)
        except httpx.TransportError as e:
            last_exc = e
            logger.warning("Transport error on %s, retrying...", url)
    raise RuntimeError(f"All retries failed for {url}") from last_exc


def fetch_debate_list_page(
    client: httpx.Client,
    cache_dir: Path,
    chamber: str,
    date_start: str,
    date_end: str,
    skip: int,
) -> dict:
    params = {
        "chamber_type": "house",
        "chamber": chamber,
        "date_start": date_start,
        "date_end": date_end,
        "limit": PAGE_SIZE,
        "skip": skip,
    }
    cache_url = DEBATES_API + "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    cached = _get_cached(cache_dir, cache_url)
    if cached:
        return json.loads(cached)

    time.sleep(REQUEST_DELAY)
    r = _fetch_with_backoff(client, DEBATES_API, params=params, timeout=30)
    _put_cache(cache_dir, cache_url, r.content)
    return r.json()


def fetch_debate_xml(client: httpx.Client, cache_dir: Path, xml_uri: str) -> bytes:
    cached = _get_cached(cache_dir, xml_uri, ".xml")
    if cached:
        return cached

    time.sleep(REQUEST_DELAY)
    r = _fetch_with_backoff(client, xml_uri, timeout=60, follow_redirects=True)
    _put_cache(cache_dir, xml_uri, r.content, ".xml")
    return r.content


def iter_debate_xmls(
    cache_dir: Path,
    chamber: str,
    date_start: str,
    date_end: str,
) -> Iterator[tuple[dict, bytes]]:
    with httpx.Client() as client:
        skip = 0
        while True:
            data = fetch_debate_list_page(
                client, cache_dir, chamber, date_start, date_end, skip
            )
            results = data.get("results", [])
            if not results:
                break

            for item in results:
                dr = item.get("debateRecord", {})
                if not dr:
                    continue
                xml_entry = dr.get("formats", {}).get("xml")
                if not xml_entry or not isinstance(xml_entry, dict):
                    continue
                xml_uri = xml_entry.get("uri")
                if not xml_uri:
                    continue
                try:
                    xml_bytes = fetch_debate_xml(client, cache_dir, xml_uri)
                    yield dr, xml_bytes
                except Exception as e:
                    logger.error("Failed to fetch XML %s: %s", xml_uri, e)

            skip += len(results)
            if len(results) < PAGE_SIZE:
                break


def debate_source_url(dr: dict) -> str:
    record_uri = dr.get("uri", "")
    if "/debateRecord/" in record_uri:
        parts = record_uri.split("/debateRecord/")[1].split("/")
        if len(parts) >= 2:
            chamber_slug, date_slug = parts[0], parts[1]
            return f"https://www.oireachtas.ie/en/debates/debate/{chamber_slug}/{date_slug}/"
    return "https://www.oireachtas.ie/en/debates/"
