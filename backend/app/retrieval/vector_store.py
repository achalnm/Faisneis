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

    if filters:
        clauses: list[dict] = []

        if "date_start" in filters and "date_end" in filters:
            clauses.append({"debate_date": {"$gte": filters["date_start"]}})
            clauses.append({"debate_date": {"$lte": filters["date_end"]}})
        elif "date_start" in filters:
            clauses.append({"debate_date": {"$gte": filters["date_start"]}})
        elif "date_end" in filters:
            clauses.append({"debate_date": {"$lte": filters["date_end"]}})

        if "chamber" in filters:
            clauses.append({"chamber": {"$eq": filters["chamber"]}})

        if "speaker_name" in filters:
            clauses.append({"speaker_name": {"$eq": filters["speaker_name"]}})

        if len(clauses) == 1:
            where = clauses[0]
        elif len(clauses) > 1:
            where = {"$and": clauses}

    query_vec = embed_one(text)
    kwargs: dict[str, Any] = {
        "query_embeddings": [query_vec],
        "n_results": k,
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
        out.append({"text": doc, "metadata": meta, "distance": dist})
    return out


def count() -> int:
    return _collection().count()
