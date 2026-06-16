import logging
from app.agent.llm import get_llm
from app.schemas import ToolPlan

logger = logging.getLogger(__name__)

_SYSTEM = """\
You route questions about Irish politics and economics to the right data sources.

Given a question, return JSON with these fields:
- intent: "speech_only" for questions about what politicians said,
  "stats_only" for official statistics questions, "both" if you need both
- speech_query: short phrase to search Dail/Seanad transcripts with, or null
- stats_topics: list of economic topic keywords (e.g. "inflation", "unemployment")
- date_start / date_end: ISO dates if a time window is mentioned, else null
- speakers: politician or party names mentioned explicitly
- rationale: one sentence explaining the decision

If a question asks your personal opinion, treat it as a search for parliamentary debate on that topic.
Unrelated questions (sports, entertainment etc) should still attempt a speech search.

Output valid JSON only, matching this shape:
{"intent": "both", "speech_query": "housing supply", "date_start": "2024-01-01", "date_end": null, "speakers": [], "stats_topics": ["house completions"], "rationale": "..."}
"""

_SCHEMA = '{"intent":"both","speech_query":"housing supply","date_start":"2024-01-01","date_end":null,"speakers":[],"stats_topics":["house completions"],"rationale":"..."}'


def route(question: str) -> ToolPlan:
    llm = get_llm()
    raw = llm.complete_json(_SYSTEM, question, schema_hint=_SCHEMA)

    intent = raw.get("intent", "both")
    if intent not in ("speech_only", "stats_only", "both"):
        intent = "both"

    return ToolPlan(
        intent=intent,
        speech_query=raw.get("speech_query"),
        date_start=raw.get("date_start"),
        date_end=raw.get("date_end"),
        speakers=raw.get("speakers") or [],
        stats_topics=raw.get("stats_topics") or [],
        rationale=raw.get("rationale", ""),
    )
