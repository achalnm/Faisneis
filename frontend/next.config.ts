import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow the backend URL to be injected at build time via NEXT_PUBLIC_API_BASE.
  // Locally this falls back to http://127.0.0.1:8000 (see api-client.ts).
};

export default nextConfig;
