"use client";

import { create } from "zustand";

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
      // Same-origin: hits the Next route handler at /api/auth/refresh-token,
      // which reads the httpOnly refresh cookie set by the login Server Action
      // and forwards it server-to-server to the backend. Browser can't send
      // the cookie directly to the backend domain (different host).
      const res = await fetch(`/api/auth/refresh-token`, {
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
      // Same-origin: hits the Next route handler at /api/auth/refresh-token,
      // which reads the httpOnly refresh cookie set by the login Server Action
      // and forwards it server-to-server to the backend. Browser can't send
      // the cookie directly to the backend domain (different host).
      const res = await fetch(`/api/auth/refresh-token`, {
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
