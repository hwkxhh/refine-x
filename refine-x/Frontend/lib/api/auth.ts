import { api, setToken } from "./client";
import type { UserResponse, Token } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Register a new user.
 */
export async function register(
  name: string,
  email: string,
  password: string,
): Promise<UserResponse> {
  return api.post<UserResponse>(
    "/auth/register",
    { name, email, password },
    { skipAuth: true },
  );
}

/**
 * Login — NOTE: backend uses OAuth2PasswordRequestForm
 * which expects application/x-www-form-urlencoded, NOT JSON.
 * The field name is "username" (not "email").
 */
export async function login(
  email: string,
  password: string,
): Promise<Token> {
  const body = new URLSearchParams({ username: email, password });

  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Login failed" }));
    throw { detail: err.detail || "Login failed", status: res.status };
  }

  const token: Token = await res.json();
  setToken(token.access_token);
  return token;
}

/**
 * Get current authenticated user.
 */
export async function getMe(): Promise<UserResponse> {
  return api.get<UserResponse>("/auth/me");
}
