import argparse
import logging
import sys
from pathlib import Path
from datetime import date

from app.config import settings
from app.ingest.oireachtas_client import iter_debate_xmls, debate_source_url
from app.ingest.akn_parser import parse_debate_xml
from app.ingest.chunker import speech_to_chunks
from app.retrieval.vector_store import add_chunks, existing_ids, count
from app.schemas import SpeechChunk

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run(chambers: list[str], date_start: str, date_end: str, dry_run: bool = False):
    cache_dir = settings.cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)

    loaded_ids = existing_ids() if not dry_run else set()

    total_new = 0
    total_skipped = 0
    total_debates = 0

    for chamber in chambers:
        logger.info("Ingesting %s from %s to %s", chamber, date_start, date_end)

        for dr, xml_bytes in iter_debate_xmls(cache_dir, chamber, date_start, date_end):
            debate_date = dr.get("date", "")
            debate_title = dr.get("house", {}).get("showAs", "Unknown")
            source_url = debate_source_url(dr)
            total_debates += 1

            speeches = parse_debate_xml(xml_bytes, debate_date, chamber, debate_title, source_url)

            new_chunks: list[SpeechChunk] = []
            for s in speeches:
                for chunk in speech_to_chunks(s):
                    if chunk.speech_id in loaded_ids:
                        total_skipped += 1
                    else:
                        new_chunks.append(chunk)
                        loaded_ids.add(chunk.speech_id)

            if new_chunks and not dry_run:
                added = add_chunks(new_chunks)
                total_new += added
            else:
                total_new += len(new_chunks)

            if total_debates % 10 == 0:
                logger.info("Processed %d debates, %d new, %d skipped",
                            total_debates, total_new, total_skipped)

    logger.info("Done. Debates: %d, new chunks: %d, skipped: %d",
                total_debates, total_new, total_skipped)
    if not dry_run:
        logger.info("Total in store: %d", count())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chamber", choices=["dail", "seanad", "both"], default="both")
    parser.add_argument("--date-start", default=settings.ingest_date_start)
    parser.add_argument("--date-end", default=settings.ingest_date_end or date.today().isoformat())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    chambers = ["dail", "seanad"] if args.chamber == "both" else [args.chamber]
    run(chambers, args.date_start, args.date_end, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
