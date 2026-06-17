"use client";

import { Answer } from "@/app/api-client";

interface Props {
  answer: Answer;
}

function scrollToFootnote(ref: string) {
  const el = document.getElementById(`footnote-${ref}`);
  if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
}

function renderParagraph(text: string, key: number) {
  const parts = text.split(/(\[[SC]\d+\])/g);
  const nodes = parts.map((part, i) => {
    const m = part.match(/^\[([SC]\d+)\]$/);
    if (m) {
      return (
        <button
          key={i}
          className="cit-marker"
          onClick={() => scrollToFootnote(m[1])}
          title={`Go to source ${m[1]}`}
        >
          {m[1]}
        </button>
      );
    }
    return <span key={i}>{part}</span>;
  });

  return (
    <p
      key={key}
      style={{
        fontFamily: "var(--font-body)",
        fontSize: 17,
        lineHeight: 1.8,
        color: "var(--color-ink)",
        margin: 0,
        paddingBottom: "1.1em",
      }}
    >
      {nodes}
    </p>
  );
}

export default function AnswerView({ answer }: Props) {
  const paragraphs = answer.answer
    .split(/\n\n+/)
    .filter((p) => p.trim().length > 0);

  return (
    <div>
      <div>
        {paragraphs.length > 0
          ? paragraphs.map((p, i) => renderParagraph(p.trim(), i))
          : renderParagraph(answer.answer, 0)}
      </div>

      {answer.caveats && answer.caveats.trim() && (
        <p
          style={{
            fontFamily: "var(--font-body)",
            fontStyle: "italic",
            fontSize: 15,
            color: "var(--color-ink-muted)",
            borderLeft: "3px solid var(--color-rule)",
            paddingLeft: 14,
            marginTop: 4,
            lineHeight: 1.7,
          }}
        >
          {answer.caveats}
        </p>
      )}
    </div>
  );
}
