"use client";

import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";
import { clearToken } from "@/lib/api/client";
import {
  login as apiLogin,
  register as apiRegister,
  getMe,
} from "@/lib/api/auth";
import type { UserResponse } from "@/lib/api/types";

/* ── Context shape ───────────────────────────────────────────────────────── */

export interface AuthContextValue {
  user: UserResponse | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue>({
  user: null,
  isLoading: true,
  login: async () => {},
  register: async () => {},
  logout: () => {},
});

/* ── Provider ─────────────────────────────────────────────────────────────── */

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /* Check for existing session on mount */
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setIsLoading(false);
      return;
    }

    getMe()
      .then(setUser)
      .catch(() => {
        clearToken();
      })
      .finally(() => setIsLoading(false));
  }, []);

  /* Login */
  const login = useCallback(async (email: string, password: string) => {
    await apiLogin(email, password);         // stores token internally
    const me = await getMe();
    setUser(me);
  }, []);

  /* Register → auto-login */
  const register = useCallback(
    async (name: string, email: string, password: string) => {
      await apiRegister(name, email, password);
      await apiLogin(email, password);
      const me = await getMe();
      setUser(me);
    },
    [],
  );

  /* Logout */
  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    window.location.href = "/auth/login";
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, isLoading, login, register, logout }),
    [user, isLoading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
