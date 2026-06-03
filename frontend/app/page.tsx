"use client";

import { useEffect, useState } from "react";
import { fetchHealth } from "./api-client";

export default function Home() {
  const [status, setStatus] = useState<string>("checking...");
  const [provider, setProvider] = useState<string>("");

  useEffect(() => {
    fetchHealth()
      .then((d) => {
        setStatus(d.status);
        setProvider(d.provider);
      })
      .catch(() => setStatus("error"));
  }, []);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-white p-8">
      <h1 className="text-3xl font-semibold text-gray-900 mb-2">Fáisnéis</h1>
      <p className="text-gray-500 mb-8 text-sm">
        Irish parliamentary debates and official statistics, cross-referenced.
      </p>
      <div className="rounded-lg border border-gray-200 px-6 py-4 text-sm text-gray-700">
        Backend status:{" "}
        <span className={status === "ok" ? "text-green-600 font-medium" : "text-red-500"}>
          {status}
        </span>
        {provider && (
          <span className="ml-3 text-gray-400">LLM provider: {provider}</span>
        )}
      </div>
    </main>
  );
}
