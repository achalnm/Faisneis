"use client";

import { ChartData } from "@/app/api-client";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { ExternalLink } from "lucide-react";

interface Props {
  data: ChartData;
}

function formatPeriod(p: string): string {
  const monthly = p.match(/^(\d{4})M(\d{2})$/);
  if (monthly) {
    const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    return `${months[parseInt(monthly[2]) - 1]} '${monthly[1].slice(2)}`;
  }
  const quarterly = p.match(/^(\d{4})Q(\d)$/);
  if (quarterly) return `Q${quarterly[2]} '${quarterly[1].slice(2)}`;
  return p.slice(0, 7);
}

export default function StatChart({ data }: Props) {
  if (!data.points || data.points.length === 0) return null;

  const step = Math.max(1, Math.floor(data.points.length / 10));

  return (
    <div
      className="mt-8"
      style={{
        borderLeft: "4px solid var(--color-green-accent)",
        background: "var(--color-parchment-dark)",
        paddingTop: 20,
        paddingBottom: 16,
        paddingLeft: 20,
        paddingRight: 20,
      }}
    >
      <div className="mb-4">
        <h3
          style={{
            fontFamily: "var(--font-display)",
            fontWeight: 700,
            fontSize: 16,
            color: "var(--color-ink)",
            lineHeight: 1.3,
          }}
        >
          {data.title}
        </h3>
        {data.units && (
          <p
            style={{
              fontFamily: "var(--font-ui)",
              fontSize: 11,
              color: "var(--color-ink-muted)",
              marginTop: 2,
              letterSpacing: "0.03em",
            }}
          >
            {data.units}
          </p>
        )}
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <LineChart
          data={data.points}
          margin={{ top: 4, right: 8, left: -8, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="2 4" stroke="var(--color-rule)" vertical={false} />
          <XAxis
            dataKey="period"
            tick={{
              fontSize: 10,
              fill: "var(--color-ink-muted)",
              fontFamily: "var(--font-ui)",
            }}
            tickFormatter={formatPeriod}
            interval={step - 1}
            axisLine={{ stroke: "var(--color-rule)" }}
            tickLine={false}
          />
          <YAxis
            tick={{
              fontSize: 10,
              fill: "var(--color-ink-muted)",
              fontFamily: "var(--font-ui)",
            }}
            width={44}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              fontFamily: "var(--font-ui)",
              fontSize: 12,
              background: "var(--color-parchment)",
              border: "1px solid var(--color-rule)",
              borderRadius: 0,
            }}
            formatter={(v) => [v, data.units || "Value"]}
            labelFormatter={(l) => formatPeriod(String(l ?? ""))}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="var(--color-green-accent)"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: "var(--color-green-dark)" }}
          />
        </LineChart>
      </ResponsiveContainer>

      {data.source_url && (
        <a
          href={data.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 mt-3"
          style={{
            fontFamily: "var(--font-ui)",
            fontSize: 11,
            color: "var(--color-ink-faint)",
            textDecoration: "none",
          }}
        >
          via CSO PxStat <ExternalLink size={10} />
        </a>
      )}
    </div>
  );
}
