"use client";

import { useState, useRef } from "react";
import { askQuestion, AskResponse } from "./api-client";
import AnswerView from "@/components/AnswerView";
import SourcesPanel from "@/components/SourcesPanel";
import StatChart from "@/components/StatChart";
import { Search, ChevronDown, ChevronUp } from "lucide-react";

const EXAMPLES = [
  "What did Irish politicians say about housing supply in 2024?",
  "How often has the cost of living been raised in the Dáil this year, and what do the inflation figures show?",
  "What has the Minister for Finance said about employment, and how does that compare to the CSO unemployment rate?",
];

export default function Home() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showReasoning, setShowReasoning] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  async function submit(q?: string) {
    const text = q ?? question;
    if (!text.trim()) return;
    if (q) setQuestion(q);
    setLoading(true);
    setError(null);
    setResult(null);
    setShowReasoning(false);
    try {
      const data = await askQuestion(text.trim());
      setResult(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      <div className="max-w-2xl mx-auto px-4 py-12">
        {/* Header */}
        <header className="mb-10 text-center">
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Fáisnéis</h1>
          <p className="mt-2 text-gray-500 text-sm max-w-md mx-auto">
            Ask about Irish parliamentary debates and official statistics together.
            Every figure and quote traces to its source.
          </p>
        </header>

        {/* Search box */}
        <div className="relative">
          <textarea
            ref={inputRef}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKey}
            rows={2}
            placeholder="Ask a question about Irish politics and economics…"
            className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 pr-12 text-sm text-gray-900 placeholder-gray-400 shadow-sm resize-none focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
          <button
            onClick={() => submit()}
            disabled={loading || !question.trim()}
            className="absolute bottom-3 right-3 p-1.5 rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-40 transition-colors"
            aria-label="Ask"
          >
            <Search size={16} />
          </button>
        </div>

        {/* Example chips */}
        <div className="mt-3 flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => submit(ex)}
              className="text-xs px-3 py-1.5 rounded-full border border-gray-200 bg-white text-gray-600 hover:border-green-400 hover:text-green-700 transition-colors"
            >
              {ex.length > 60 ? ex.slice(0, 57) + "…" : ex}
            </button>
          ))}
        </div>

        {/* Loading */}
        {loading && (
          <div className="mt-10 flex items-center gap-3 text-gray-400 text-sm">
            <span className="inline-block w-4 h-4 border-2 border-gray-200 border-t-green-600 rounded-full animate-spin" />
            Searching debates and statistics…
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Result */}
        {result && !loading && (
          <div className="mt-8 space-y-2">
            {/* Answer */}
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
              <AnswerView answer={result.answer} />
            </div>

            {/* Chart */}
            {result.chart_data && (
              <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
                <StatChart data={result.chart_data} />
              </div>
            )}

            {/* Sources */}
            {(result.answer.speech_citations.length > 0 ||
              result.answer.stat_citations.length > 0) && (
              <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
                <SourcesPanel
                  speechCitations={result.answer.speech_citations}
                  statCitations={result.answer.stat_citations}
                />
              </div>
            )}

            {/* Reasoning toggle */}
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
              <button
                onClick={() => setShowReasoning(!showReasoning)}
                className="w-full flex items-center justify-between px-5 py-3 text-xs text-gray-500 hover:text-gray-700 transition-colors"
              >
                <span className="font-medium uppercase tracking-wide">How this was answered</span>
                {showReasoning ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
              {showReasoning && (
                <div className="px-5 pb-4 text-xs text-gray-600 space-y-1.5 border-t border-gray-50">
                  <p>
                    <span className="font-medium text-gray-700">Intent</span>{" "}
                    {result.tool_plan.intent}
                  </p>
                  {result.tool_plan.speech_query && (
                    <p>
                      <span className="font-medium text-gray-700">Speech query</span>{" "}
                      {result.tool_plan.speech_query}
                    </p>
                  )}
                  {result.tool_plan.stats_topics.length > 0 && (
                    <p>
                      <span className="font-medium text-gray-700">Stats topics</span>{" "}
                      {result.tool_plan.stats_topics.join(", ")}
                    </p>
                  )}
                  <p>
                    <span className="font-medium text-gray-700">Rationale</span>{" "}
                    {result.tool_plan.rationale}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Footer */}
        <footer className="mt-16 pt-6 border-t border-gray-100 text-xs text-gray-400 space-y-1 text-center">
          <p>
            Parliamentary debates under the Houses of the Oireachtas Open Data PSI Licence.
          </p>
          <p>Statistics &copy; Central Statistics Office, Ireland.</p>
        </footer>
      </div>
    </div>
  );
}
