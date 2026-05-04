import { cookies } from "next/headers";
import { NextResponse } from "next/server";

/**
 * Same-origin proxy for the backend refresh-token endpoint.
 *
 * Why this exists:
 *   The login flow runs as a Server Action ("/auth/actions.ts"), which sets
 *   the refresh_token cookie on the *frontend* origin (e.g.
 *   `4fcvshzh-3000.euw.devtunnels.ms`). When the browser later wants to
 *   refresh the access token by calling the backend directly on a different
 *   origin (e.g. `4fcvshzh-8000.euw.devtunnels.ms`), the browser does NOT
 *   send the cookie — it belongs to a different host. devtunnels.ms is on
 *   the Public Suffix List, so we can't share a cookie via a parent domain.
 *
 *   This route handler runs on the frontend origin, reads the cookie that
 *   the Server Action set, and forwards it to the backend in a
 *   server-to-server fetch. New tokens are written back as cookies on the
 *   frontend origin, keeping the same flow as the login Server Action.
 */

const getApiUrl = () => {
  const envUrl =
    process.env.API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000";
  return envUrl.replace(/\/$/, "");
};

export async function POST() {
  const cookieStore = await cookies();
  const refreshToken = cookieStore.get("refresh_token")?.value;

  if (!refreshToken) {
    return NextResponse.json(
      { detail: "Refresh token missing" },
      { status: 401 },
    );
  }

  let backendRes: Response;
  try {
    backendRes = await fetch(`${getApiUrl()}/api/auth/refresh-token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // Forward the cookie that the browser cannot send cross-origin itself.
        Cookie: `refresh_token=${refreshToken}`,
      },
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 },
    );
  }

  if (!backendRes.ok) {
    const err = await backendRes.json().catch(() => ({}));
    // Refresh failed — clear stale cookies so the client can drop to login.
    cookieStore.delete("refresh_token");
    cookieStore.delete("access_token");
    return NextResponse.json(
      { detail: err.detail || "Refresh failed" },
      { status: backendRes.status },
    );
  }

  const data = await backendRes.json();

  // Rotate cookies on the frontend origin (same as login Server Action does).
  cookieStore.set("refresh_token", data.refresh_token, {
    maxAge: 7 * 24 * 60 * 60,
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
  });
  cookieStore.set("access_token", data.access_token, {
    maxAge: 15 * 60,
    httpOnly: false,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
  });

  return NextResponse.json({ access_token: data.access_token });
}
