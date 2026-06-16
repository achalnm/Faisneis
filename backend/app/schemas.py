from pydantic import BaseModel, Field
from typing import Optional


class SpeechChunk(BaseModel):
    speech_id: str
    text: str
    speaker_name: str
    member_uri: str | None = None
    party: str | None = None
    role: str | None = None
    chamber: str
    debate_title: str
    debate_date: str
    topic_section: str | None = None
    source_url: str


class ToolPlan(BaseModel):
    intent: str
    speech_query: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    speakers: list[str] = Field(default_factory=list)
    stats_topics: list[str] = Field(default_factory=list)
    rationale: str


class SpeechCitation(BaseModel):
    ref: str
    speaker: str
    party: str | None = None
    date: str
    debate_title: str
    quote_or_paraphrase: str
    source_url: str


class StatCitation(BaseModel):
    ref: str
    matrix: str
    title: str
    units: str
    value_or_range: str
    period: str
    source_url: str


class ChartPoint(BaseModel):
    period: str
    value: float


class ChartData(BaseModel):
    title: str
    units: str
    points: list[ChartPoint]
    source_url: str


class Answer(BaseModel):
    answer: str
    speech_citations: list[SpeechCitation] = Field(default_factory=list)
    stat_citations: list[StatCitation] = Field(default_factory=list)
    confidence: str
    caveats: str


class AskResponse(BaseModel):
    tool_plan: ToolPlan
    answer: Answer
    chart_data: Optional[ChartData] = None
