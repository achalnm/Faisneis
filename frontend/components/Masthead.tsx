import TricolourStripe from "./TricolourStripe";

function LeinsterHouse({
  className = "",
  style,
}: {
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <svg
      viewBox="0 0 280 100"
      fill="currentColor"
      className={className}
      style={style}
      aria-hidden="true"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* left wing */}
      <rect x="0" y="46" width="60" height="54" />
      <rect x="8"  y="48" width="3" height="52" opacity="0.45" />
      <rect x="20" y="48" width="3" height="52" opacity="0.45" />
      <rect x="32" y="48" width="3" height="52" opacity="0.45" />
      <rect x="44" y="48" width="3" height="52" opacity="0.45" />

      {/* right wing */}
      <rect x="220" y="46" width="60" height="54" />
      <rect x="228" y="48" width="3" height="52" opacity="0.45" />
      <rect x="240" y="48" width="3" height="52" opacity="0.45" />
      <rect x="252" y="48" width="3" height="52" opacity="0.45" />
      <rect x="264" y="48" width="3" height="52" opacity="0.45" />

      {/* main block */}
      <rect x="54" y="10" width="172" height="90" />

      {/* pediment */}
      <polygon points="96,10 140,1 184,10" />

      {/* flag */}
      <rect x="139" y="0" width="2" height="3" />

      {/* columns */}
      <rect x="76"  y="24" width="4" height="76" opacity="0.45" />
      <rect x="93"  y="24" width="4" height="76" opacity="0.45" />
      <rect x="110" y="24" width="4" height="76" opacity="0.45" />
      <rect x="127" y="24" width="4" height="76" opacity="0.45" />
      <rect x="144" y="24" width="4" height="76" opacity="0.45" />
      <rect x="161" y="24" width="4" height="76" opacity="0.45" />
      <rect x="178" y="24" width="4" height="76" opacity="0.45" />

      {/* steps */}
      <rect x="102" y="96" width="76" height="3" />
      <rect x="110" y="93" width="60" height="4" />
    </svg>
  );
}

export default function Masthead() {
  return (
    <header
      className="relative w-full overflow-hidden"
      style={{ background: "var(--color-green-dark)" }}
    >
      <div
        className="absolute bottom-0 left-1/2 pointer-events-none"
        style={{ transform: "translateX(-50%)", opacity: 0.06, width: "min(900px, 100%)" }}
      >
        <LeinsterHouse style={{ width: "100%", height: "auto", display: "block" }} />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <LeinsterHouse
              style={{
                height: 26,
                width: "auto",
                color: "var(--color-cream)",
                opacity: 0.8,
                flexShrink: 0,
                display: "block",
              }}
            />
            <div>
              <h1 style={{
                fontFamily: "var(--font-display)",
                fontSize: "clamp(26px, 4.5vw, 50px)",
                fontWeight: 700,
                color: "var(--color-cream)",
                lineHeight: 1,
                letterSpacing: "-0.01em",
                margin: 0,
              }}>
                Fáisnéis
              </h1>
              <p style={{
                fontFamily: "var(--font-ui)",
                fontSize: 11,
                color: "var(--color-cream)",
                opacity: 0.6,
                letterSpacing: "0.04em",
                marginTop: 5,
              }}>
                Parliamentary intelligence. Every claim sourced.
              </p>
            </div>
          </div>

          <div
            className="hidden sm:flex flex-col items-end gap-1"
            style={{
              fontFamily: "var(--font-ui)",
              fontSize: 10,
              letterSpacing: "0.13em",
              textTransform: "uppercase",
              color: "var(--color-cream)",
              opacity: 0.5,
              flexShrink: 0,
            }}
          >
            <span>Dáil Éireann</span>
            <span>Seanad Éireann</span>
            <span>CSO PxStat</span>
          </div>
        </div>
      </div>

      <TricolourStripe />
    </header>
  );
}
