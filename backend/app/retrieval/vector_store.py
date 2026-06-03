"""
Chroma persistent store for speech chunks. One collection: "speeches".

Metadata stored per chunk mirrors SpeechChunk fields. Filters on query
can narrow by debate_date range, chamber, or speaker_name.
"""

import logging
from functools import lru_cache
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.schemas import SpeechChunk
from app.retrieval.embeddings import embed, embed_one

logger = logging.getLogger(__name__)

COLLECTION = "speeches"
BATCH_SIZE = 128


@lru_cache(maxsize=1)
def _client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(
        path=str(settings.chroma_dir),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _collection():
    return _client().get_or_create_collection(
        COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def existing_ids() -> set[str]:
    col = _collection()
    result = col.get(include=[])  # just IDs
    return set(result["ids"])


def add_chunks(chunks: list[SpeechChunk]) -> int:
    if not chunks:
        return 0

    col = _collection()
    added = 0

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c.text for c in batch]
        vectors = embed(texts)
        ids = [c.speech_id for c in batch]
        metadatas = [
            {
                "speaker_name": c.speaker_name,
                "member_uri": c.member_uri or "",
                "party": c.party or "",
                "role": c.role or "",
                "chamber": c.chamber,
                "debate_title": c.debate_title,
                "debate_date": c.debate_date,
                "topic_section": c.topic_section or "",
                "source_url": c.source_url,
            }
            for c in batch
        ]
        col.add(ids=ids, embeddings=vectors, documents=texts, metadatas=metadatas)
        added += len(batch)

    return added


def query(
    text: str,
    k: int = 10,
    filters: dict[str, Any] | None = None,
) -> list[dict]:
    """
    Semantic search over speeches. Returns a list of result dicts, each
    containing the document text, metadata, and distance.

    filters can include:
      date_start / date_end  -- ISO strings for debate_date range
      chamber                -- "dail" or "seanad"
      speaker_name           -- exact match
    """
    col = _collection()
    where: dict[str, Any] | None = None

    # Chroma 1.x only supports $eq on strings. Date ranges and speaker filters
    # are applied in Python after retrieval. Pull more results than k so there
    # are enough candidates once post-filtering is done.
    date_start = filters.get("date_start") if filters else None
    date_end = filters.get("date_end") if filters else None
    speaker_filter = filters.get("speaker_name") if filters else None

    if filters:
        clauses: list[dict] = []
        if "chamber" in filters:
            clauses.append({"chamber": {"$eq": filters["chamber"]}})
        if len(clauses) == 1:
            where = clauses[0]
        elif len(clauses) > 1:
            where = {"$and": clauses}

    # Fetch more candidates when we know post-filtering will drop some
    fetch_k = k * 4 if (date_start or date_end or speaker_filter) else k

    query_vec = embed_one(text)
    kwargs: dict[str, Any] = {
        "query_embeddings": [query_vec],
        "n_results": min(fetch_k, col.count() or 1),
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where

    try:
        results = col.query(**kwargs)
    except Exception as e:
        logger.error("Chroma query failed: %s", e)
        return []

    out = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        d = meta.get("debate_date", "")
        if date_start and d < date_start:
            continue
        if date_end and d > date_end:
            continue
        if speaker_filter and meta.get("speaker_name", "").lower() != speaker_filter.lower():
            continue
        out.append({"text": doc, "metadata": meta, "distance": dist})
        if len(out) >= k:
            break

    return out


def count() -> int:
    return _collection().count()
