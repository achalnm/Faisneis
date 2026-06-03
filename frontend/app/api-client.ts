const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json() as Promise<{ status: string; provider: string }>;
}

export interface SpeechCitation {
  ref: string;
  speaker: string;
  party: string | null;
  date: string;
  debate_title: string;
  quote_or_paraphrase: string;
  source_url: string;
}

export interface StatCitation {
  ref: string;
  matrix: string;
  title: string;
  units: string;
  value_or_range: string;
  period: string;
  source_url: string;
}

export interface ChartPoint {
  period: string;
  value: number;
}

export interface ChartData {
  title: string;
  units: string;
  points: ChartPoint[];
  source_url: string;
}

export interface ToolPlan {
  intent: string;
  speech_query: string | null;
  date_start: string | null;
  date_end: string | null;
  speakers: string[];
  stats_topics: string[];
  rationale: string;
}

export interface Answer {
  answer: string;
  speech_citations: SpeechCitation[];
  stat_citations: StatCitation[];
  confidence: "high" | "medium" | "low";
  caveats: string;
}

export interface AskResponse {
  tool_plan: ToolPlan;
  answer: Answer;
  chart_data: ChartData | null;
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const res = await fetch(`${API_BASE}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Server error ${res.status}`);
  }
  return res.json();
}
