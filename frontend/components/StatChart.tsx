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

export default function StatChart({ data }: Props) {
  if (!data.points || data.points.length === 0) return null;

  const stride = Math.max(1, Math.floor(data.points.length / 48));

  return (
    <div className="mt-6 border border-gray-100 rounded-xl p-4">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-800">{data.title}</h3>
          {data.units && (
            <p className="text-xs text-gray-400 mt-0.5">{data.units}</p>
          )}
        </div>
        <a
          href={data.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-xs text-green-600 hover:underline shrink-0 ml-2"
        >
          Source: CSO <ExternalLink size={11} />
        </a>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data.points} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="period"
            tick={{ fontSize: 10, fill: "#9ca3af" }}
            interval="preserveStartEnd"
            tickFormatter={(v) => v.slice(0, 7)}
          />
          <YAxis tick={{ fontSize: 10, fill: "#9ca3af" }} width={48} />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 6, borderColor: "#e5e7eb" }}
            formatter={(v) => [v, data.units || "Value"]}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#16a34a"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
