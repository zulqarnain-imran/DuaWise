import type { NextConfig } from "next";

const apiTarget = process.env.DUA_API_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // The Python recommendation service is not reachable at build time on Vercel, so
  // rewrites must be lazy and must never be exercised during `next build`.
  async rewrites() {
    return [
      { source: "/api/engine/:path*", destination: `${apiTarget}/:path*` },
    ];
  },
  async headers() {
    return [
      {
        source: "/sw.js",
        headers: [
          { key: "Cache-Control", value: "no-cache, no-store, must-revalidate" },
        ],
      },
    ];
  },
};

export default nextConfig;
