"""
Splits speech dicts into embeddable chunks and validates them against
the SpeechChunk schema.

Most speeches fit in one chunk. Speeches over ~500 tokens are split into
overlapping windows so context is preserved across chunk boundaries.
"""

from app.schemas import SpeechChunk

# Approximate token count: 4 chars per token is a reasonable estimate
# for English/Irish parliamentary text.
CHARS_PER_TOKEN = 4
MAX_TOKENS = 500
OVERLAP_TOKENS = 80

MAX_CHARS = MAX_TOKENS * CHARS_PER_TOKEN
OVERLAP_CHARS = OVERLAP_TOKENS * CHARS_PER_TOKEN


def _split_words(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        # Accumulate words until we hit the char limit
        buf = []
        char_count = 0
        i = start
        while i < len(words):
            w = words[i]
            if char_count + len(w) + 1 > max_chars and buf:
                break
            buf.append(w)
            char_count += len(w) + 1
            i += 1

        if not buf:
            # Single word longer than the limit, take it anyway
            buf = [words[start]]
            i = start + 1

        chunks.append(" ".join(buf))

        # Step back by overlap so next chunk has context
        overlap_buf = []
        overlap_chars_acc = 0
        for w in reversed(buf):
            if overlap_chars_acc + len(w) + 1 > overlap_chars:
                break
            overlap_buf.insert(0, w)
            overlap_chars_acc += len(w) + 1

        # Advance start past the non-overlapping portion
        start = i - len(overlap_buf)
        if start <= (i - len(buf)):
            # No progress — safety valve
            start = i

    return chunks


def speech_to_chunks(speech: dict) -> list[SpeechChunk]:
    text = speech["text"]
    base_id = speech["speech_id"]

    if len(text) <= MAX_CHARS:
        return [SpeechChunk(**{**speech, "speech_id": base_id})]

    parts = _split_words(text, MAX_CHARS, OVERLAP_CHARS)
    chunks = []
    for idx, part in enumerate(parts, start=1):
        chunk_id = f"{base_id}#{idx}"
        chunks.append(SpeechChunk(**{**speech, "speech_id": chunk_id, "text": part}))
    return chunks
