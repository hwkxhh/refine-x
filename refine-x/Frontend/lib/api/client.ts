/* ─── RefineX API Client ────────────────────────────────────────────────── */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ── helpers ─────────────────────────────────────────────────────────────── */

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setToken(token: string) {
  localStorage.setItem("access_token", token);
}

export function clearToken() {
  localStorage.removeItem("access_token");
}

/* ── generic typed fetch wrapper ─────────────────────────────────────────── */

export interface ApiError {
  detail: string;
  status: number;
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit & { skipAuth?: boolean } = {},
): Promise<T> {
  const { skipAuth, headers: extraHeaders, ...fetchOpts } = options;

  const headers: Record<string, string> = {
    ...(extraHeaders as Record<string, string>),
  };

  // Default to JSON content-type unless caller overrides (e.g. FormData)
  if (!headers["Content-Type"] && !(fetchOpts.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  // Attach auth token
  const token = getToken();
  if (token && !skipAuth) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${endpoint}`, { ...fetchOpts, headers });

  // 401 → clear session, redirect
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") {
      window.location.href = "/auth/login";
    }
    throw { detail: "Session expired. Please log in again.", status: 401 } as ApiError;
  }

  // Other errors
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw { detail: body.detail || `HTTP ${res.status}`, status: res.status } as ApiError;
  }

  // 204 No Content
  if (res.status === 204) return undefined as unknown as T;

  return res.json() as Promise<T>;
}

/* ── convenience methods ─────────────────────────────────────────────────── */

export const api = {
  get<T>(endpoint: string, opts?: RequestInit & { skipAuth?: boolean }) {
    return apiClient<T>(endpoint, { method: "GET", ...opts });
  },

  post<T>(endpoint: string, body?: unknown, opts?: RequestInit & { skipAuth?: boolean }) {
    return apiClient<T>(endpoint, {
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body),
      ...opts,
    });
  },

  put<T>(endpoint: string, body?: unknown, opts?: RequestInit & { skipAuth?: boolean }) {
    return apiClient<T>(endpoint, {
      method: "PUT",
      body: JSON.stringify(body),
      ...opts,
    });
  },

  delete<T>(endpoint: string, opts?: RequestInit & { skipAuth?: boolean }) {
    return apiClient<T>(endpoint, { method: "DELETE", ...opts });
  },
};
