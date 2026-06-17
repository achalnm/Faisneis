export default function LoadingState() {
  return (
    <div
      className="w-full py-12 px-6"
      style={{ background: "var(--color-parchment)" }}
    >
      <div className="max-w-3xl mx-auto">
        <p
          className="mb-8"
          style={{
            fontFamily: "var(--font-display)",
            fontStyle: "italic",
            fontSize: 18,
            color: "var(--color-ink-muted)",
          }}
        >
          Searching the record&hellip;
        </p>

        <div className="space-y-7">
          <div className="space-y-2">
            <div className="flex gap-4 items-baseline">
              <div className="shimmer-line h-3 rounded-none" style={{ width: 140 }} />
              <div className="shimmer-line h-2.5 rounded-none" style={{ width: 80, opacity: 0.6 }} />
            </div>
            <div className="shimmer-line h-2.5 rounded-none" style={{ width: "100%" }} />
            <div className="shimmer-line h-2.5 rounded-none" style={{ width: "87%" }} />
            <div className="shimmer-line h-2.5 rounded-none" style={{ width: "73%" }} />
          </div>

          <div className="space-y-2">
            <div className="flex gap-4 items-baseline">
              <div className="shimmer-line h-3 rounded-none" style={{ width: 120 }} />
              <div className="shimmer-line h-2.5 rounded-none" style={{ width: 90, opacity: 0.6 }} />
            </div>
            <div className="shimmer-line h-2.5 rounded-none" style={{ width: "100%" }} />
            <div className="shimmer-line h-2.5 rounded-none" style={{ width: "95%" }} />
            <div className="shimmer-line h-2.5 rounded-none" style={{ width: "61%" }} />
          </div>

          <div className="space-y-2">
            <div className="flex gap-4 items-baseline">
              <div className="shimmer-line h-3 rounded-none" style={{ width: 160 }} />
              <div className="shimmer-line h-2.5 rounded-none" style={{ width: 70, opacity: 0.6 }} />
            </div>
            <div className="shimmer-line h-2.5 rounded-none" style={{ width: "100%" }} />
            <div className="shimmer-line h-2.5 rounded-none" style={{ width: "82%" }} />
          </div>
        </div>

        <p
          className="mt-10"
          style={{
            fontFamily: "var(--font-ui)",
            fontSize: 12,
            color: "var(--color-ink-faint)",
          }}
        >
          If the server was idle, the first request may take up to a minute to wake.
        </p>
      </div>
    </div>
  );
}
