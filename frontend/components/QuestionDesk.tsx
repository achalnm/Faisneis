"use client";

import { useRef } from "react";

const EXAMPLES = [
  "What did TDs say about housing supply in 2024?",
  "How has rent changed, and what did politicians promise?",
  "What is the CSO unemployment rate vs what the Dáil discussed?",
];

interface Props {
  question: string;
  setQuestion: (q: string) => void;
  onSubmit: (q?: string) => void;
  loading: boolean;
}

export default function QuestionDesk({ question, setQuestion, onSubmit, loading }: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  }

  return (
    <section
      className="w-full"
      style={{ background: "#ffffff", borderBottom: "1px solid var(--color-rule)" }}
    >
      <div className="max-w-3xl mx-auto px-6 py-10">
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKey}
            rows={2}
            placeholder="Ask the Dáil a question…"
            className="question-input"
            disabled={loading}
            aria-label="Your question"
          />
        </div>

        <div className="flex items-center justify-between mt-4 flex-wrap gap-3">
          <button
            onClick={() => onSubmit()}
            disabled={loading || !question.trim()}
            style={{
              background: "var(--color-green-dark)",
              color: "var(--color-cream)",
              fontFamily: "var(--font-ui)",
              fontSize: 13,
              fontWeight: 600,
              letterSpacing: "0.04em",
              padding: "9px 22px",
              border: "none",
              borderRadius: 0,
              cursor: loading || !question.trim() ? "not-allowed" : "pointer",
              opacity: loading || !question.trim() ? 0.45 : 1,
              transition: "background 150ms ease, opacity 150ms ease",
            }}
            onMouseEnter={(e) => {
              if (!loading && question.trim())
                (e.currentTarget as HTMLButtonElement).style.background = "var(--color-green-mid)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = "var(--color-green-dark)";
            }}
          >
            Ask
          </button>

          <span
            style={{
              fontFamily: "var(--font-ui)",
              fontSize: 11,
              color: "var(--color-ink-faint)",
              letterSpacing: "0.02em",
            }}
          >
            Searching 315,000 Dáil &amp; Seanad speeches + live CSO data
          </span>
        </div>

        <div className="flex flex-wrap gap-2 mt-6">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              className="example-chip"
              onClick={() => onSubmit(ex)}
              disabled={loading}
            >
              {ex}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
