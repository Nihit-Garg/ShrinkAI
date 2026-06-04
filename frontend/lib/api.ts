/**
 * Central API helper.
 *
 * All requests go through /api/* which Next.js proxies to the FastAPI backend
 * (see next.config.ts). This means the browser makes same-origin requests —
 * no CORS, no preflight failures, no browser blocking.
 *
 * For production: set BACKEND_URL in your server environment so next.config.ts
 * proxies to the correct backend host.
 */

const BASE_URL = "/api";

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem("token");

  // Only attach Content-Type for requests that have a body.
  const hasBody = options.body !== undefined && options.body !== null;
  const contentTypeHeader: Record<string, string> = hasBody ? { "Content-Type": "application/json" } : {};
  const authHeader: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

  const headers: Record<string, string> = {
    ...contentTypeHeader,
    ...authHeader,
    ...(options.headers as Record<string, string> || {}),
  };

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // Auto-logout on 401 — clears stale/expired tokens and redirects to /auth
  if (response.status === 401) {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    if (typeof window !== "undefined") {
      window.location.href = "/auth";
    }
    throw new Error("Session expired. Please sign in again.");
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Request failed (${response.status})`
    );
  }

  return response.json();
}
