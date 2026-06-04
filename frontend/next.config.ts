import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    // Proxy all /api/* requests to the FastAPI backend.
    // This runs server-side so the browser never makes a cross-origin request → no CORS.
    const backendUrl =
      process.env.BACKEND_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
