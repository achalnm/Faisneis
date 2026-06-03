"use client";

import { SpeechCitation, StatCitation } from "@/app/api-client";
import { ExternalLink } from "lucide-react";

interface Props {
  speechCitations: SpeechCitation[];
  statCitations: StatCitation[];
}

export default function SourcesPanel({ speechCitations, statCitations }: Props) {
  if (speechCitations.length === 0 && statCitations.length === 0) return null;

  return (
    <div className="space-y-6 mt-6">
      {speechCitations.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
            From the Oireachtas
          </h3>
          <ul className="space-y-3">
            {speechCitations.map((c) => (
              <li
                key={c.ref}
                id={`cite-${c.ref}`}
                className="border border-gray-100 rounded-lg p-3 text-sm scroll-mt-20"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <span className="font-medium text-gray-800">{c.speaker}</span>
                    {c.party && (
                      <span className="ml-1.5 text-xs text-gray-400">({c.party})</span>
                    )}
                    <span className="ml-2 text-gray-400 text-xs">{c.date}</span>
                    <p className="text-gray-500 text-xs mt-0.5 truncate">{c.debate_title}</p>
                    {c.quote_or_paraphrase && (
                      <p className="mt-1.5 text-gray-700 italic text-xs leading-relaxed">
                        &ldquo;{c.quote_or_paraphrase}&rdquo;
                      </p>
                    )}
                  </div>
                  <a
                    href={c.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="shrink-0 text-green-600 hover:text-green-700"
                    title="Open debate"
                  >
                    <ExternalLink size={14} />
                  </a>
                </div>
                <span className="inline-block mt-1 text-[10px] font-semibold text-green-700 bg-green-50 rounded px-1">
                  {c.ref}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {statCitations.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
            From the CSO
          </h3>
          <ul className="space-y-3">
            {statCitations.map((c) => (
              <li
                key={c.ref}
                id={`cite-${c.ref}`}
                className="border border-gray-100 rounded-lg p-3 text-sm scroll-mt-20"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <span className="font-medium text-gray-800">{c.title}</span>
                    <p className="text-gray-500 text-xs mt-0.5">
                      {c.value_or_range} {c.units && `(${c.units})`} &mdash; {c.period}
                    </p>
                    <p className="text-gray-400 text-xs mt-0.5">Matrix: {c.matrix}</p>
                  </div>
                  <a
                    href={c.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="shrink-0 text-green-600 hover:text-green-700"
                    title="Open CSO table"
                  >
                    <ExternalLink size={14} />
                  </a>
                </div>
                <span className="inline-block mt-1 text-[10px] font-semibold text-green-700 bg-green-50 rounded px-1">
                  {c.ref}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
