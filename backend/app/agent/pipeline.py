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


def answer(question: str) -> AskResponse:
    plan = route(question)
    logger.info("Tool plan: intent=%s, speech_query=%r, stats=%s",
                plan.intent, plan.speech_query, plan.stats_topics)

    speech_chunks: list[dict] = []
    stat_results: list[dict] = []

    if plan.intent in ("speech_only", "both") and plan.speech_query:
        filters = _build_speech_filters(plan)
        speech_chunks = vector_query(plan.speech_query, k=TOP_K_SPEECHES, filters=filters or None)
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
