import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

from app.config import settings

if not settings.pinecone_api_key:
    print("PINECONE_API_KEY not set in .env")
    sys.exit(1)

import chromadb
from chromadb.config import Settings as ChromaSettings
from pinecone import Pinecone, ServerlessSpec

BATCH = 100


def main():
    logger.info("Reading from Chroma at %s", settings.chroma_dir)
    client = chromadb.PersistentClient(
        path=str(settings.chroma_dir),
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    col = client.get_or_create_collection("speeches")
    total = col.count()
    logger.info("Chroma has %d vectors", total)

    pc = Pinecone(api_key=settings.pinecone_api_key)
    existing = [i.name for i in pc.list_indexes()]
    if settings.pinecone_index not in existing:
        logger.info("Creating index %s", settings.pinecone_index)
        pc.create_index(
            name=settings.pinecone_index,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        time.sleep(10)

    idx = pc.Index(settings.pinecone_index)

    uploaded = 0
    offset = 0
    while offset < total:
        result = col.get(
            limit=BATCH,
            offset=offset,
            include=["embeddings", "documents", "metadatas"],
        )
        ids = result["ids"]
        if not ids:
            break

        records = []
        for rid, vec, doc, meta in zip(
            ids,
            result["embeddings"],
            result["documents"],
            result["metadatas"],
        ):
            m = dict(meta)
            m["text"] = (doc or "")[:1000]
            records.append({"id": rid, "values": [float(x) for x in vec], "metadata": m})

        idx.upsert(vectors=records)
        uploaded += len(records)
        offset += BATCH

        if uploaded % 1000 == 0 or uploaded == total:
            logger.info("Uploaded %d / %d", uploaded, total)

    logger.info("Done. %d vectors in Pinecone.", uploaded)


if __name__ == "__main__":
    main()
