import logging
from typing import Any
from functools import lru_cache

from app.config import settings
from app.schemas import SpeechChunk
from app.retrieval.embeddings import embed, embed_one

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


@lru_cache(maxsize=1)
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


def existing_ids() -> set[str]:
    idx = _pinecone_index()
    ids: set[str] = set()
    try:
        for batch in idx.list():
            ids.update(batch)
    except Exception:
        pass
    return ids


def add_chunks(chunks: list[SpeechChunk]) -> int:
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


def query(text: str, k: int = 10, filters: dict[str, Any] | None = None) -> list[dict]:
    idx = _pinecone_index()
    q_vec = embed_one(text)

    date_start = filters.get("date_start") if filters else None
    date_end = filters.get("date_end") if filters else None
    chamber = filters.get("chamber") if filters else None
    speaker = filters.get("speaker_name") if filters else None

    clauses = {}
    if chamber:
        clauses["chamber"] = {"$eq": chamber}
    if speaker:
        clauses["speaker_name"] = {"$eq": speaker}
    pc_filter = clauses if clauses else None

    fetch_k = k * 4 if (date_start or date_end or speaker) else k
    resp = idx.query(vector=q_vec, top_k=fetch_k, include_metadata=True, filter=pc_filter)

    out = []
    # date filtering in Python because range queries on string dates via Pinecone metadata
    # were returning unexpected results
    for match in resp.matches:
        meta = match.metadata or {}
        d = meta.get("debate_date", "")
        if date_start and d < date_start:
            continue
        if date_end and d > date_end:
            continue
        out.append({
            "text": meta.get("text", ""),
            "metadata": {key: val for key, val in meta.items() if key != "text"},
            "distance": 1 - match.score,
        })
        if len(out) >= k:
            break
    return out


def count() -> int:
    try:
        stats = _pinecone_index().describe_index_stats()
        return stats.total_vector_count
    except Exception:
        return -1
