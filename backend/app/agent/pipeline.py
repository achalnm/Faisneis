import logging
from datetime import date
from pathlib import Path
from typing import Any

from app.config import settings
from app.agent.router import route
from app.agent.synthesize import synthesize
from app.retrieval.vector_store import query as vector_query
from app.stats.cso_catalog import build_catalog, search_catalog, get_best_matrix
from app.stats.cso_client import fetch_dataset, dataset_source_url
from app.stats.jsonstat import extract_series
from app.schemas import AskResponse, ChartData, ChartPoint, ToolPlan

logger = logging.getLogger(__name__)

TOP_K_SPEECHES = 5

_GREETINGS = {
    "hello", "hi", "hey", "hiya", "howya", "howdy", "sup", "yo",
    "hi there", "hello there", "hey there", "good morning", "good afternoon",
    "good evening", "morning", "afternoon", "evening",
}

_THANKS = {
    "thanks", "thank you", "thank you so much", "thanks a lot", "thanks a million",
    "cheers", "ta", "thx", "ty", "many thanks", "much appreciated", "appreciated",
    "brilliant", "deadly", "savage", "class", "legend", "sound",
}

_GOODBYES = {
    "bye", "goodbye", "good bye", "see ya", "see you", "cya", "later",
    "take care", "talk later", "bye bye", "adios", "cheerio", "good night",
    "goodnight", "night", "ttyl", "tty later",
}

_PRAISE = {
    "wow", "amazing", "awesome", "impressive", "nice", "great", "cool", "okay", "ok",
    "good", "excellent", "fantastic", "love it", "love this", "this is great",
    "this is amazing", "this is cool", "well done", "nice work", "good work",
    "great work", "very cool", "pretty cool", "not bad",
}

_NEGATIVE = {
    "i hate you", "hate you", "hate this", "this is rubbish", "rubbish",
    "this is useless", "useless", "this is trash", "trash", "garbage",
    "this doesn't work", "doesn't work", "not working", "broken", "this is broken",
    "terrible", "awful", "horrible", "this is terrible", "this is awful",
    "worst", "this is the worst", "bad", "this is bad", "you're bad",
    "shut up", "shut it", "go away", "leave me alone", "f off", "off",
    "stupid", "you're stupid", "dumb", "idiot",
}

_ABOUT = {
    "what are you", "who are you", "what is this", "what is faisneis",
    "what does this do", "what can you do", "what do you do",
    "how does this work", "how do you work", "explain yourself",
    "tell me about yourself", "tell me about this", "what's this",
    "whats this", "who made this", "who built this", "how were you made",
}

_CONFUSED = {
    "what", "huh", "hmm", "hm", "eh", "pardon", "sorry", "what?", "huh?",
    "i don't understand", "i dont understand", "confused", "not sure",
    "what do you mean", "idk",
}

_TEST = {
    "test", "testing", "hello world", "ping", "123", "1234",
    "asdf", "qwerty", "asd", "lol", "lmao", "haha", "hehe",
}


def _quick_reply(text: str, rationale: str) -> AskResponse:
    from app.schemas import Answer, ToolPlan
    return AskResponse(
        tool_plan=ToolPlan(intent="speech_only", speech_query=None, date_start=None,
                           date_end=None, speakers=[], stats_topics=[], rationale=rationale),
        answer=Answer(answer=text, speech_citations=[], stat_citations=[],
                      confidence="high", caveats=""),
        chart_data=None,
    )


def _classify(q: str) -> str | None:
    n = q.lower().strip().rstrip("!?.,")
    if n in _GREETINGS:
        return "greeting"
    if n in _THANKS:
        return "thanks"
    if n in _GOODBYES:
        return "goodbye"
    if n in _PRAISE:
        return "praise"
    if n in _NEGATIVE:
        return "negative"
    if n in _ABOUT:
        return "about"
    if n in _CONFUSED:
        return "confused"
    if n in _TEST:
        return "test"
    # single char/number or pure gibberish
    if len(n) <= 1:
        return "short"
    words = n.split()
    if len(words) <= 2 and all(len(w) <= 3 for w in words):
        return "short"
    return None

_ROLE_WORDS = {
    "minister", "taoiseach", "tánaiste", "tanaiste", "senator", "deputy",
    "chair", "chairman", "secretary", "general", "finance", "health",
    "education", "justice", "housing", "transport", "environment",
}


def _is_person_name(s: str) -> bool:
    words = s.lower().split()
    role_count = sum(1 for w in words if w in _ROLE_WORDS)
    return role_count < len(words) / 2


def _build_speech_filters(plan: ToolPlan) -> dict:
    filters: dict[str, Any] = {}
    if plan.date_start:
        filters["date_start"] = plan.date_start
    if plan.date_end:
        filters["date_end"] = plan.date_end
    if len(plan.speakers) == 1 and _is_person_name(plan.speakers[0]):
        filters["speaker_name"] = plan.speakers[0]
    return filters


def _fetch_stat(topic: str, plan: ToolPlan) -> dict | None:
    cache_dir = settings.cache_dir
    matrix = get_best_matrix(topic, cache_dir)
    if not matrix:
        logger.warning("No matrix found for topic %r", topic)
        return None

    try:
        ds = fetch_dataset(matrix, cache_dir)
    except Exception as e:
        logger.error("Failed to fetch dataset %s: %s", matrix, e)
        return None

    period_start = None
    period_end = None
    if plan.date_start:
        period_start = plan.date_start.replace("-", "")[:6]
    if plan.date_end:
        period_end = plan.date_end.replace("-", "")[:6]

    if not period_start:
        today = date.today()
        period_start = f"{today.year - 3}{today.month:02d}"

    result = extract_series(ds, period_start=period_start, period_end=period_end)

    if result["series"]:
        sample = result["series"][0]
        extra_dims = [k for k in sample.keys() if k not in ("period", "value")]
        for dim in extra_dims:
            agg_value = next(
                (v for v in ("All items", "All", "State", "Ireland") if
                 any(s.get(dim) == v for s in result["series"])),
                None,
            )
            if agg_value:
                result["series"] = [s for s in result["series"] if s.get(dim) == agg_value]
                break

    return result


_REPLIES = {
    "greeting": "Hey! Ask me anything about Irish parliamentary debates or statistics. Housing, rent, immigration, cost of living, health, education, whatever you're curious about.",
    "thanks":   "No problem, glad it helped! Ask another question any time.",
    "goodbye":  "Take care! Come back any time you want to look something up.",
    "praise":   "Cheers! Let me know if you want to dig into anything else.",
    "negative": "Fair enough. If you do want to give it a proper try, ask something like 'What did politicians say about rent?' and see what comes back.",
    "about":    "Faisneis searches Dail and Seanad debate transcripts from 2020 onwards and cross-references them with live CSO statistics. Type any question about Irish politics or economics and it finds the relevant speeches with citations back to the original source.",
    "confused": "Try typing a question about Irish politics or economics and I'll search the debates for you. Something like 'What did politicians say about housing?' or 'How has rent changed in Ireland?'",
    "test":     "Yep, working fine. Try asking a real question, something like 'What did politicians say about the cost of living?'",
    "short":    "That's a bit short to search on. Try a full question like 'What did politicians say about housing?' or 'How has unemployment changed in Ireland?'",
}


def answer(question: str) -> AskResponse:
    category = _classify(question)
    if category:
        return _quick_reply(_REPLIES[category], category)

    plan = route(question)
    logger.info("Tool plan: intent=%s, speech_query=%r, stats=%s",
                plan.intent, plan.speech_query, plan.stats_topics)

    speech_chunks: list[dict] = []
    stat_results: list[dict] = []

    if plan.intent in ("speech_only", "both") and plan.speech_query:
        filters = _build_speech_filters(plan)
        # If all speakers are roles (not person names), strip them from the query
        # so role words don't bias the semantic search away from topical content.
        sq = plan.speech_query
        if plan.speakers and not any(_is_person_name(s) for s in plan.speakers):
            for speaker in plan.speakers:
                sq = sq.replace(speaker, "").strip()
        if not sq:
            sq = plan.speech_query
        speech_chunks = vector_query(sq, k=TOP_K_SPEECHES, filters=filters or None)
        logger.info("Retrieved %d speech chunks", len(speech_chunks))

    if plan.intent in ("stats_only", "both") and plan.stats_topics:
        for topic in plan.stats_topics:
            result = _fetch_stat(topic, plan)
            if result and result.get("series"):
                stat_results.append(result)
        logger.info("Retrieved %d stat series", len(stat_results))

    answer_obj = synthesize(question, speech_chunks, stat_results)

    chart_data: ChartData | None = None
    for sr in stat_results:
        series = sr.get("series", [])
        if len(series) >= 3:
            chart_data = ChartData(
                title=sr.get("title", ""),
                units=sr.get("units", ""),
                points=[ChartPoint(period=p["period"], value=p["value"]) for p in series],
                source_url=sr.get("source_url", ""),
            )
            break

    return AskResponse(tool_plan=plan, answer=answer_obj, chart_data=chart_data)
