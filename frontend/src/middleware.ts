import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";

const ADMIN_TOKEN = process.env.ADMIN_TOKEN ?? "";
const ADMIN_COOKIE = "divai_admin";

export default async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // ── Admin auth ────────────────────────────────────────────────────────────
  if (pathname.startsWith("/admin")) {
    if (pathname === "/admin/login" || pathname.startsWith("/api/admin-auth")) {
      return NextResponse.next();
    }
    const cookie = request.cookies.get(ADMIN_COOKIE)?.value;
    if (!cookie || cookie !== ADMIN_TOKEN) {
      const url = new URL("/admin/login", request.url);
      url.searchParams.set("from", pathname);
      return NextResponse.redirect(url);
    }
    return NextResponse.next();
  }

  // ── User session refresh (Supabase) ───────────────────────────────────────
  // Supabase SSR requires the middleware to refresh the session cookie on
  // every request so the JWT doesn't expire mid-session.
  let response = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return request.cookies.getAll(); },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          );
          response = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  // Refresh session — required for Server Components to see auth state
  await supabase.auth.getUser();

  // Protect /history — redirect to /login if not authenticated
  if (pathname.startsWith("/history")) {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      const url = new URL("/login", request.url);
      url.searchParams.set("from", pathname);
      return NextResponse.redirect(url);
    }
  }

  return response;
}

export const config = {
  matcher: [
    "/admin/:path*",
    "/history/:path*",
    // Refresh session on all non-static routes
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
