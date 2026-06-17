"use client";

import { useState } from "react";
import { askQuestion, AskResponse, ToolPlan } from "./api-client";
import Masthead from "@/components/Masthead";
import QuestionDesk from "@/components/QuestionDesk";
import LoadingState from "@/components/LoadingState";
import AnswerView from "@/components/AnswerView";
import SourcesPanel from "@/components/SourcesPanel";
import StatChart from "@/components/StatChart";
import TricolourStripe from "@/components/TricolourStripe";
import { ChevronDown, ChevronUp } from "lucide-react";

// badge
function ConfidenceBadge({ level }: { level: "high" | "medium" | "low" }) {
  const config = {
    high:   { borderColor: "#169B62", textColor: "#0d5e38", label: "High confidence" },
    medium: { borderColor: "#c27a00", textColor: "#7a4d00", label: "Medium confidence" },
    low:    { borderColor: "#c0392b", textColor: "#7b1e1e", label: "Low confidence" },
  }[level] ?? { borderColor: "#999", textColor: "#555", label: level };

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        borderLeft: `3px solid ${config.borderColor}`,
        paddingLeft: 8,
        fontFamily: "var(--font-ui)",
        fontSize: 11,
        letterSpacing: "0.07em",
        textTransform: "uppercase",
        color: config.textColor,
        fontWeight: 600,
      }}
    >
      {level === "high" && <span className="live-dot" />}
      {config.label}
    </span>
  );
}

// editor thing
function EditorNote({ toolPlan, open, onToggle }: { toolPlan: ToolPlan; open: boolean; onToggle: () => void }) {
  return (
    <div
      className="mt-10"
      style={{ background: "#ece7da", border: "1px solid var(--color-rule)" }}
    >
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full px-4 py-3"
        style={{ background: "transparent", border: "none", cursor: "pointer" }}
      >
        <span style={{
          fontFamily: "var(--font-ui)",
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          color: "var(--color-ink-muted)",
        }}>
          Editor&rsquo;s Note
        </span>
        {open ? <ChevronUp size={13} color="var(--color-ink-muted)" /> : <ChevronDown size={13} color="var(--color-ink-muted)" />}
      </button>

      <div className="editor-note-body" style={{ maxHeight: open ? 300 : 0 }}>
        <div
          className="px-4 pb-4 space-y-1.5"
          style={{
            fontFamily: "var(--font-ui)",
            fontSize: 12,
            color: "var(--color-ink-muted)",
            borderTop: "1px solid var(--color-rule)",
            paddingTop: 12,
          }}
        >
          <p><span style={{ fontWeight: 600, color: "var(--color-ink)" }}>intent</span>&nbsp; {toolPlan.intent}</p>
          {toolPlan.speech_query && (
            <p><span style={{ fontWeight: 600, color: "var(--color-ink)" }}>query</span>&nbsp; {toolPlan.speech_query}</p>
          )}
          {toolPlan.speakers.length > 0 && (
            <p><span style={{ fontWeight: 600, color: "var(--color-ink)" }}>speakers</span>&nbsp; {toolPlan.speakers.join(", ")}</p>
          )}
          {toolPlan.stats_topics.length > 0 && (
            <p><span style={{ fontWeight: 600, color: "var(--color-ink)" }}>topics</span>&nbsp; {toolPlan.stats_topics.join(", ")}</p>
          )}
          <p><span style={{ fontWeight: 600, color: "var(--color-ink)" }}>why</span>&nbsp; {toolPlan.rationale}</p>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [askedQ, setAskedQ] = useState("");
  const [editorOpen, setEditorOpen] = useState(false);

  async function submit(q?: string) {
    const text = (q ?? question).trim();
    if (!text) return;
    if (q) setQuestion(q);
    setLoading(true);
    setError(null);
    setResult(null);
    setAskedQ(text);
    setEditorOpen(false);
    try {
      const data = await askQuestion(text);
      setResult(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "couldn't fetch the answer");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--color-parchment)" }}>
      <Masthead />

      <QuestionDesk
        question={question}
        setQuestion={setQuestion}
        onSubmit={submit}
        loading={loading}
      />

      <main className="flex-1 w-full">
        {loading && <LoadingState />}

        {error && !loading && (
          <div className="max-w-3xl mx-auto px-6 py-10">
            <div style={{ borderLeft: "3px solid #c0392b", paddingLeft: 14, paddingTop: 10, paddingBottom: 10 }}>
              <p style={{ fontFamily: "var(--font-ui)", fontSize: 13, color: "#7b1e1e" }}>
                {error}
              </p>
              <button
                onClick={() => submit()}
                style={{
                  fontFamily: "var(--font-ui)",
                  fontSize: 12,
                  color: "var(--color-green-accent)",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: 0,
                  marginTop: 8,
                  textDecoration: "underline",
                }}
              >
                try again
              </button>
            </div>
          </div>
        )}

        {result && !loading && (
          <div className="w-full" style={{ background: "var(--color-parchment)" }}>
            <article className="max-w-3xl mx-auto px-6 py-10">
              <header className="mb-6">
                <h2 style={{
                  fontFamily: "var(--font-display)",
                  fontWeight: 700,
                  fontSize: "clamp(22px, 4vw, 30px)",
                  color: "var(--color-ink)",
                  lineHeight: 1.25,
                  letterSpacing: "-0.01em",
                  marginBottom: 14,
                }}>
                  {askedQ}
                </h2>

                <div
                  className="flex flex-wrap items-center gap-x-5 gap-y-2"
                  style={{
                    fontFamily: "var(--font-ui)",
                    fontSize: 11,
                    letterSpacing: "0.06em",
                    textTransform: "uppercase",
                    color: "var(--color-ink-muted)",
                  }}
                >
                  <span>Oireachtas debates &middot; CSO PxStat</span>
                  <ConfidenceBadge level={result.answer.confidence} />
                </div>

                <div style={{ height: 1, background: "var(--color-ink)", marginTop: 12, marginBottom: 2 }} />
                <div style={{ height: 1, background: "var(--color-rule)", marginTop: 3 }} />
              </header>

              <AnswerView answer={result.answer} />

              {result.chart_data && <StatChart data={result.chart_data} />}

              {(result.answer.speech_citations.length > 0 || result.answer.stat_citations.length > 0) && (
                <SourcesPanel
                  speechCitations={result.answer.speech_citations}
                  statCitations={result.answer.stat_citations}
                />
              )}

              <EditorNote
                toolPlan={result.tool_plan}
                open={editorOpen}
                onToggle={() => setEditorOpen((v) => !v)}
              />
            </article>
          </div>
        )}
      </main>

      <footer style={{ background: "var(--color-green-dark)" }}>
        <TricolourStripe />
        <div className="max-w-5xl mx-auto px-6 py-10">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
            <div>
              <h3 style={{
                fontFamily: "var(--font-ui)",
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                color: "var(--color-cream)",
                opacity: 0.5,
                marginBottom: 10,
              }}>
                Data
              </h3>
              <p style={{ fontFamily: "var(--font-ui)", fontSize: 12, color: "var(--color-cream)", opacity: 0.6, lineHeight: 1.6 }}>
                Dail and Seanad debates from the Oireachtas open data licence.
              </p>
              <p style={{ fontFamily: "var(--font-ui)", fontSize: 12, color: "var(--color-cream)", opacity: 0.6, lineHeight: 1.6, marginTop: 6 }}>
                Stats from CSO Ireland, open data.
              </p>
            </div>

            <div>
              <h3 style={{
                fontFamily: "var(--font-display)",
                fontWeight: 700,
                fontSize: 18,
                color: "var(--color-cream)",
                marginBottom: 10,
              }}>
                Fáisnéis
              </h3>
              <p style={{ fontFamily: "var(--font-ui)", fontSize: 12, color: "var(--color-cream)", opacity: 0.6, lineHeight: 1.6 }}>
                315k speeches from the Dail and Seanad. Links back to the actual debate.
              </p>
            </div>

            <div>
              <h3 style={{
                fontFamily: "var(--font-ui)",
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                color: "var(--color-cream)",
                opacity: 0.5,
                marginBottom: 10,
              }}>
                Built for Ireland
              </h3>
              <p style={{ fontFamily: "var(--font-ui)", fontSize: 12, color: "var(--color-cream)", opacity: 0.6, lineHeight: 1.6 }}>
                all open source data
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
