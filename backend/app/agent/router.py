import logging
from app.agent.llm import get_llm
from app.schemas import ToolPlan

logger = logging.getLogger(__name__)

_SYSTEM = """\
You are a query router for a system that answers questions about Irish politics
and economics. Given a user question, produce a JSON routing plan.

Rules:
- Use intent "speech_only" if the question is purely about what politicians said.
- Use intent "stats_only" if the question is purely about official statistics.
- Use intent "both" if it involves both political statements and statistical evidence.
- If the question asks your personal opinion ("what do you think", "do you agree"), treat it as a search for relevant parliamentary debate on that topic instead.
- If the question is completely unrelated to Irish politics or economics (sports results, entertainment, etc), still attempt a speech search — the synthesizer will handle it gracefully.
- speech_query should be a short phrase optimised for semantic search over debate transcripts.
- stats_topics should list the economic topic(s) to look up (e.g. "inflation", "unemployment").
- date_start / date_end should be ISO dates (YYYY-MM-DD) if the question implies a time window, else null.
- speakers should list politician names or party names mentioned explicitly.
- rationale is one sentence explaining your routing decision.

Output JSON matching exactly this shape:
{
  "intent": "speech_only" | "stats_only" | "both",
  "speech_query": string | null,
  "date_start": string | null,
  "date_end": string | null,
  "speakers": [string],
  "stats_topics": [string],
  "rationale": string
}
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
