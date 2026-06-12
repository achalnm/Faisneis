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
  // Uses SSE so heartbeat comments keep the connection alive through proxies/Render timeout.
  const res = await fetch(`${API_BASE}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Server error ${res.status}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop() ?? "";
    let eventType = "";
    let dataLine = "";
    for (const line of lines) {
      if (line.startsWith("event: ")) eventType = line.slice(7).trim();
      else if (line.startsWith("data: ")) dataLine = line.slice(6).trim();
      else if (line === "" && dataLine) {
        const payload = JSON.parse(dataLine);
        if (eventType === "error") throw new Error(payload.detail ?? "Server error");
        if (eventType === "result") return payload as AskResponse;
        eventType = "";
        dataLine = "";
      }
    }
  }
  throw new Error("Stream ended without a result");
}
