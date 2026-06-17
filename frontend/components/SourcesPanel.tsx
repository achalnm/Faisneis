"use client";

import { SpeechCitation, StatCitation } from "@/app/api-client";
import { ExternalLink } from "lucide-react";

interface Props {
  speechCitations: SpeechCitation[];
  statCitations: StatCitation[];
}

function SpeechCard({ c }: { c: SpeechCitation }) {
  return (
    <div
      id={`footnote-${c.ref}`}
      className="footnote-card scroll-mt-24"
      style={{
        borderLeft: "3px solid var(--color-green-accent)",
        padding: "10px 10px 10px 14px",
        background: "var(--color-parchment-dark)",
      }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2 flex-wrap">
            <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 13, color: "var(--color-green-dark)" }}>
              {c.ref}
            </span>
            <span style={{ fontFamily: "var(--font-ui)", fontWeight: 600, fontSize: 13, color: "var(--color-ink)" }}>
              {c.speaker}
            </span>
            {c.party && (
              <span style={{ fontFamily: "var(--font-body)", fontStyle: "italic", fontSize: 12, color: "var(--color-ink-muted)" }}>
                ({c.party})
              </span>
            )}
            <span style={{ fontFamily: "var(--font-ui)", fontSize: 11, color: "var(--color-ink-muted)" }}>
              {c.date}
            </span>
          </div>

          {c.debate_title && (
            <p className="mt-0.5 truncate" style={{ fontFamily: "var(--font-ui)", fontSize: 11, color: "var(--color-ink-muted)" }}>
              {c.debate_title}
            </p>
          )}

          {c.quote_or_paraphrase && (
            <p className="mt-2" style={{ fontFamily: "var(--font-body)", fontStyle: "italic", fontSize: 13, color: "var(--color-ink)", lineHeight: 1.6 }}>
              &ldquo;{c.quote_or_paraphrase}&rdquo;
            </p>
          )}
        </div>

        {c.source_url && (
          <a href={c.source_url} target="_blank" rel="noopener noreferrer"
            className="shrink-0 flex items-center gap-1"
            style={{ fontFamily: "var(--font-ui)", fontSize: 11, color: "var(--color-green-accent)", textDecoration: "none", whiteSpace: "nowrap" }}
            title="Open in Oireachtas"
          >
            Oireachtas <ExternalLink size={11} />
          </a>
        )}
      </div>
    </div>
  );
}

function StatCard({ c }: { c: StatCitation }) {
  return (
    <div
      id={`footnote-${c.ref}`}
      className="footnote-card scroll-mt-24"
      style={{
        borderLeft: "3px solid var(--color-orange-accent)",
        padding: "12px 10px 10px 14px",
        background: "var(--color-parchment-dark)",
      }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2 flex-wrap">
            <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 13, color: "#b85c00" }}>
              {c.ref}
            </span>
            <span style={{ fontFamily: "var(--font-ui)", fontWeight: 600, fontSize: 13, color: "var(--color-ink)" }}>
              {c.title}
            </span>
          </div>

          <p className="mt-1" style={{ fontFamily: "var(--font-ui)", fontSize: 12, color: "var(--color-ink-muted)" }}>
            {c.value_or_range}{c.units ? ` ${c.units}` : ""} &middot; {c.period}
          </p>

          <p style={{ fontFamily: "var(--font-ui)", fontSize: 11, color: "var(--color-ink-faint)", marginTop: 2 }}>
            Matrix {c.matrix}
          </p>
        </div>

        {c.source_url && (
          <a href={c.source_url} target="_blank" rel="noopener noreferrer"
            className="shrink-0 flex items-center gap-1"
            style={{ fontFamily: "var(--font-ui)", fontSize: 11, color: "var(--color-orange-accent)", textDecoration: "none", whiteSpace: "nowrap" }}
            title="Open CSO table"
          >
            CSO <ExternalLink size={11} />
          </a>
        )}
      </div>
    </div>
  );
}

export default function SourcesPanel({ speechCitations, statCitations }: Props) {
  if (speechCitations.length === 0 && statCitations.length === 0) return null;

  return (
    <div className="mt-8">
      <div className="flex items-center gap-3 mb-6">
        <div style={{ flex: 1, height: 1, background: "var(--color-rule)" }} />
        <span style={{
          fontFamily: "var(--font-ui)",
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          color: "var(--color-ink-muted)",
        }}>
          Sources
        </span>
        <div style={{ flex: 1, height: 1, background: "var(--color-rule)" }} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {speechCitations.map(c => <SpeechCard key={c.ref} c={c} />)}
        {statCitations.map(c => <StatCard key={c.ref} c={c} />)}
      </div>
    </div>
  );
}
