import { NextRequest, NextResponse } from "next/server";

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;
  const isPublicRoute =
    path === "/auth/login" || path === "/auth/register" || path === "/";
  const token = request.cookies.get("refresh_token")?.value;

  // Protect private routes
  if (!isPublicRoute && !token) {
    return NextResponse.redirect(new URL("/auth/login", request.url));
  }

  // Redirect away from login if already authenticated
  if ((path === "/auth/login" || path === "/auth/register") && token) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
