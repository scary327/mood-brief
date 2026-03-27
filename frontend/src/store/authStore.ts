"use client";

import { create } from "zustand";

const getApiBase = () => {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!envUrl) return "http://localhost:8000";
  return envUrl.replace(/\/$/, "");
};

const API_BASE = getApiBase();

export interface User {
  id: string;
  email: string;
  username: string;
  created_at: string;
}

interface AuthStore {
  /* ── State ── */
  accessToken: string | null;
  user: User | null;
  isAuthenticated: boolean;

  /* ── Actions ── */
  setAccessToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  initializeAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  // Initial state
  accessToken: null,
  user: null,
  isAuthenticated: false,

  // State setters
  setAccessToken: (token) => set({ accessToken: token }),

  setUser: (user) => set({ user, isAuthenticated: !!user }),

  // Logout
  logout: () => {
    set({
      accessToken: null,
      user: null,
      isAuthenticated: false,
    });
  },

  // Refresh token using refresh cookie
  refreshToken: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/refresh-token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include", // Automatically sends refresh_token cookie
      });

      if (!res.ok) {
        // Refresh failed - user needs to re-login
        set({
          accessToken: null,
          user: null,
          isAuthenticated: false,
        });
        return false;
      }

      const data = await res.json();
      set({ accessToken: data.access_token });
      return true;
    } catch (e) {
      set({
        accessToken: null,
        user: null,
        isAuthenticated: false,
      });
      return false;
    }
  },

  // Initialize auth on app load
  initializeAuth: async () => {
    try {
      // Try to refresh token using cookie
      const res = await fetch(`${API_BASE}/api/auth/refresh-token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });

      if (res.ok) {
        const data = await res.json();
        set({
          accessToken: data.access_token,
          isAuthenticated: true,
        });
      } else {
        set({ isAuthenticated: false });
      }
    } catch (e) {
      set({ isAuthenticated: false });
    }
  },
}));
