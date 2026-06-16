import json
import logging
from app.agent.llm import get_llm
from app.schemas import Answer, SpeechCitation, StatCitation

logger = logging.getLogger(__name__)

_SYSTEM = """\
You answer questions about Irish politics and economics using ONLY the sources
provided below. You must never invent facts, figures, quotes, dates, or
statistics. If the provided sources do not support a claim, you do not make it.

Citation rules:
- Mark every claim drawn from a speech with [S1], [S2], etc.
- Mark every statistic drawn from a CSO table with [C1], [C2], etc.
- Keep direct speech quotes to one sentence at most; prefer paraphrase with attribution.
- Keep the answer field under 300 words. Be concise, cite more, explain less.
- If the data is insufficient to answer the question, say so plainly and suggest
  what additional data would be needed. Do not fabricate a substitute.

Return JSON matching exactly this shape:
{
  "answer": "prose with inline [S1]/[C1] markers",
  "speech_citations": [
    {
      "ref": "S1",
      "speaker": "Name",
      "party": "Party or null",
      "date": "YYYY-MM-DD",
      "debate_title": "...",
      "quote_or_paraphrase": "...",
      "source_url": "https://..."
    }
  ],
  "stat_citations": [
    {
      "ref": "C1",
      "matrix": "CPM01",
      "title": "Consumer Price Index",
      "units": "...",
      "value_or_range": "...",
      "period": "...",
      "source_url": "https://data.cso.ie/table/CPM01"
    }
  ],
  "confidence": "high" | "medium" | "low",
  "caveats": "honest note on what the data does not show"
}

Confidence guide: "high" when multiple corroborating sources are present and
directly address the question; "medium" when sources are partial or indirect;
"low" when sources are scarce or only tangentially relevant.
"""


def _format_speeches(chunks: list[dict]) -> str:
    if not chunks:
        return "No speech sources retrieved."
    lines = []
    for i, c in enumerate(chunks, start=1):
        m = c.get("metadata", {})
        text = c.get("text", "")
        if len(text) > 400:
            text = text[:397] + "..."
        lines.append(
            f"[S{i}] {m.get('speaker_name','?')} ({m.get('debate_date','?')}, "
            f"{m.get('chamber','?')}, {m.get('debate_title','?')})\n"
            f"Section: {m.get('topic_section') or 'unspecified'}\n"
            # truncating at 400 chars -- tried 500 but the prompt got too long
            f"Text: {text}\n"
            f"URL: {m.get('source_url','')}"
        )
    return "\n\n".join(lines)


def _format_stats(stat_results: list[dict]) -> str:
    if not stat_results:
        return "No statistical sources retrieved."
    lines = []
    for i, sr in enumerate(stat_results, start=1):
        series = sr.get("series", [])
        sample = series[-6:] if len(series) > 6 else series
        sample_str = ", ".join(f"{p['period']}={p['value']}" for p in sample)
        lines.append(
            f"[C{i}] {sr.get('title','?')} (matrix: {sr.get('matrix','?')})\n"
            f"Units: {sr.get('units','?')}\n"
            f"Recent data: {sample_str}\n"
            f"URL: {sr.get('source_url','')}"
        )
    return "\n\n".join(lines)


def synthesize(question: str, speech_chunks: list[dict], stat_results: list[dict]) -> Answer:
    speeches_text = _format_speeches(speech_chunks)
    stats_text = _format_stats(stat_results)

    user_prompt = f"""\
Question: {question}

SPEECH SOURCES (from Oireachtas debates):
{speeches_text}

STATISTICAL SOURCES (from the CSO):
{stats_text}

Write a grounded answer using only the above sources. Use [S1],[S2] for speech
citations and [C1],[C2] for stat citations. Respond with JSON only.
"""

    llm = get_llm()
    raw = llm.complete_json(_SYSTEM, user_prompt)

    speech_cits = []
    for sc in raw.get("speech_citations", []):
        try:
            ref_num = int(sc.get("ref", "S0").lstrip("S")) - 1
            chunk = speech_chunks[ref_num] if 0 <= ref_num < len(speech_chunks) else {}
            meta = chunk.get("metadata", {})
            speech_cits.append(
                SpeechCitation(
                    ref=sc.get("ref", ""),
                    speaker=meta.get("speaker_name") or sc.get("speaker", ""),
                    party=meta.get("party") or sc.get("party") or None,
                    date=meta.get("debate_date") or sc.get("date", ""),
                    debate_title=meta.get("debate_title") or sc.get("debate_title", ""),
                    quote_or_paraphrase=sc.get("quote_or_paraphrase", ""),
                    source_url=meta.get("source_url") or sc.get("source_url", ""),
                )
            )
        except Exception as e:
            logger.warning("Could not build speech citation %s: %s", sc.get("ref"), e)

    stat_cits = []
    for sc in raw.get("stat_citations", []):
        try:
            ref_num = int(sc.get("ref", "C0").lstrip("C")) - 1
            sr = stat_results[ref_num] if 0 <= ref_num < len(stat_results) else {}
            stat_cits.append(
                StatCitation(
                    ref=sc.get("ref", ""),
                    matrix=sr.get("matrix") or sc.get("matrix", ""),
                    title=sr.get("title") or sc.get("title", ""),
                    units=sr.get("units") or sc.get("units", ""),
                    value_or_range=sc.get("value_or_range", ""),
                    period=sc.get("period", ""),
                    source_url=sr.get("source_url") or sc.get("source_url", ""),
                )
            )
        except Exception as e:
            logger.warning("Could not build stat citation %s: %s", sc.get("ref"), e)

    confidence = raw.get("confidence", "low")
    if confidence not in ("high", "medium", "low"):
        confidence = "low"

    return Answer(
        answer=raw.get("answer", ""),
        speech_citations=speech_cits,
        stat_citations=stat_cits,
        confidence=confidence,
        caveats=raw.get("caveats", ""),
    )
