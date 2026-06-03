import logging
from typing import Any
from functools import lru_cache

from app.config import settings
from app.schemas import SpeechChunk
from app.retrieval.embeddings import embed, embed_one

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


def _pinecone_index():
    from pinecone import Pinecone, ServerlessSpec
    pc = Pinecone(api_key=settings.pinecone_api_key)
    existing = [i.name for i in pc.list_indexes()]
    if settings.pinecone_index not in existing:
        logger.info("Creating Pinecone index %s", settings.pinecone_index)
        pc.create_index(
            name=settings.pinecone_index,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(settings.pinecone_index)


def _pc_add_chunks(chunks: list[SpeechChunk]) -> int:
    idx = _pinecone_index()
    added = 0
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i: i + BATCH_SIZE]
        vectors = embed([c.text for c in batch])
        records = [
            {
                "id": c.speech_id,
                "values": v,
                "metadata": {
                    "text": c.text[:1000],
                    "speaker_name": c.speaker_name,
                    "member_uri": c.member_uri or "",
                    "party": c.party or "",
                    "role": c.role or "",
                    "chamber": c.chamber,
                    "debate_title": c.debate_title,
                    "debate_date": c.debate_date,
                    "topic_section": c.topic_section or "",
                    "source_url": c.source_url,
                },
            }
            for c, v in zip(batch, vectors)
        ]
        idx.upsert(vectors=records)
        added += len(batch)
    return added


def _pc_existing_ids() -> set[str]:
    return set()


def _pc_query(text: str, k: int, filters: dict | None) -> list[dict]:
    idx = _pinecone_index()
    q_vec = embed_one(text)

    pc_filter: dict | None = None
    date_start = filters.get("date_start") if filters else None
    date_end = filters.get("date_end") if filters else None
    chamber = filters.get("chamber") if filters else None
    speaker = filters.get("speaker_name") if filters else None

    clauses = {}
    if chamber:
        clauses["chamber"] = {"$eq": chamber}
    if speaker:
        clauses["speaker_name"] = {"$eq": speaker}
    if clauses:
        pc_filter = clauses

    fetch_k = k * 4 if (date_start or date_end) else k
    resp = idx.query(vector=q_vec, top_k=fetch_k, include_metadata=True, filter=pc_filter)

    out = []
    for match in resp.matches:
        meta = match.metadata or {}
        d = meta.get("debate_date", "")
        if date_start and d < date_start:
            continue
        if date_end and d > date_end:
            continue
        out.append({
            "text": meta.get("text", ""),
            "metadata": {k: v for k, v in meta.items() if k != "text"},
            "distance": 1 - match.score,
        })
        if len(out) >= k:
            break
    return out


def _pc_count() -> int:
    try:
        stats = _pinecone_index().describe_index_stats()
        return stats.total_vector_count
    except Exception:
        return -1


@lru_cache(maxsize=1)
def _chroma_collection():
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    client = chromadb.PersistentClient(
        path=str(settings.chroma_dir),
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(
        "speeches", metadata={"hnsw:space": "cosine"}
    )


def _chroma_add_chunks(chunks: list[SpeechChunk]) -> int:
    col = _chroma_collection()
    added = 0
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i: i + BATCH_SIZE]
        vectors = embed([c.text for c in batch])
        col.add(
            ids=[c.speech_id for c in batch],
            embeddings=vectors,
            documents=[c.text for c in batch],
            metadatas=[
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
            ],
        )
        added += len(batch)
    return added


def _chroma_existing_ids() -> set[str]:
    return set(_chroma_collection().get(include=[])["ids"])


def _chroma_query(text: str, k: int, filters: dict | None) -> list[dict]:
    col = _chroma_collection()
    date_start = filters.get("date_start") if filters else None
    date_end = filters.get("date_end") if filters else None
    speaker = filters.get("speaker_name") if filters else None
    chamber = filters.get("chamber") if filters else None

    where = None
    if chamber:
        where = {"chamber": {"$eq": chamber}}

    fetch_k = min(k * 4 if (date_start or date_end or speaker) else k, col.count() or 1)
    q_vec = embed_one(text)

    kwargs: dict[str, Any] = {
        "query_embeddings": [q_vec],
        "n_results": fetch_k,
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
        if speaker and meta.get("speaker_name", "").lower() != speaker.lower():
            continue
        out.append({"text": doc, "metadata": meta, "distance": dist})
        if len(out) >= k:
            break
    return out


def _chroma_count() -> int:
    return _chroma_collection().count()


def _use_pinecone() -> bool:
    return bool(settings.pinecone_api_key)


def existing_ids() -> set[str]:
    if _use_pinecone():
        return _pc_existing_ids()
    return _chroma_existing_ids()


def add_chunks(chunks: list[SpeechChunk]) -> int:
    if _use_pinecone():
        return _pc_add_chunks(chunks)
    return _chroma_add_chunks(chunks)


def query(text: str, k: int = 10, filters: dict[str, Any] | None = None) -> list[dict]:
    if _use_pinecone():
        return _pc_query(text, k, filters)
    return _chroma_query(text, k, filters)


def count() -> int:
    if _use_pinecone():
        return _pc_count()
    return _chroma_count()
