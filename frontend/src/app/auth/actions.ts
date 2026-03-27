"use server";

import { cookies } from "next/headers";

const getApiUrl = () => {
  const envUrl =
    process.env.API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000";
  return envUrl.replace(/\/$/, "");
};

export async function loginUser(email: string, password: string) {
  try {
    const res = await fetch(`${getApiUrl()}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      cache: "no-store",
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return {
        success: false,
        error: err.detail || err.error || "Неверный логин или пароль",
      };
    }

    const data = await res.json();
    const cookieStore = await cookies();

    cookieStore.set("refresh_token", data.refresh_token, {
      maxAge: 7 * 24 * 60 * 60,
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      path: "/",
    });

    cookieStore.set("access_token", data.access_token, {
      maxAge: 15 * 60,
      httpOnly: false,
      secure: process.env.NODE_ENV === "production",
      path: "/",
    });

    return { success: true };
  } catch (e: any) {
    return {
      success: false,
      error: "Ошибка сети. Проверьте подключение к серверу.",
    };
  }
}

export async function registerUser(
  email: string,
  username: string,
  password: string,
) {
  try {
    const res = await fetch(`${getApiUrl()}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, username, password }),
      cache: "no-store",
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return {
        success: false,
        error: err.detail || err.error || "Ошибка регистрации",
      };
    }

    const data = await res.json();
    const cookieStore = await cookies();

    cookieStore.set("refresh_token", data.refresh_token, {
      maxAge: 7 * 24 * 60 * 60,
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      path: "/",
    });

    cookieStore.set("access_token", data.access_token, {
      maxAge: 15 * 60,
      httpOnly: false,
      secure: process.env.NODE_ENV === "production",
      path: "/",
    });

    return { success: true };
  } catch (e: any) {
    return {
      success: false,
      error: "Ошибка сети. Проверьте подключение к серверу.",
    };
  }
}
