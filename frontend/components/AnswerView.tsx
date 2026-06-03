"use client";

import { Answer } from "@/app/api-client";

interface Props {
  answer: Answer;
}

// Replaces [S1], [C1] etc. with superscript anchor links that jump to the citation
function renderAnswer(text: string) {
  const parts = text.split(/(\[[SC]\d+\])/g);
  return parts.map((part, i) => {
    const m = part.match(/^\[([SC]\d+)\]$/);
    if (m) {
      const ref = m[1];
      return (
        <a
          key={i}
          href={`#cite-${ref}`}
          className="text-green-700 text-xs font-semibold align-super ml-0.5 hover:underline"
        >
          [{ref}]
        </a>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

const confidenceStyles: Record<string, string> = {
  high: "bg-green-100 text-green-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-red-100 text-red-800",
};

export default function AnswerView({ answer }: Props) {
  return (
    <div className="space-y-4">
      <p className="text-gray-900 leading-relaxed text-base">
        {renderAnswer(answer.answer)}
      </p>

      <div className="flex items-center gap-3 pt-1">
        <span
          className={`text-xs font-medium px-2 py-0.5 rounded-full ${
            confidenceStyles[answer.confidence] ?? "bg-gray-100 text-gray-600"
          }`}
        >
          {answer.confidence} confidence
        </span>
      </div>

      {answer.caveats && (
        <p className="text-sm text-gray-500 italic border-l-2 border-gray-200 pl-3">
          {answer.caveats}
        </p>
      )}
    </div>
  );
}
