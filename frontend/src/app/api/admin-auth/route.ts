import { NextRequest, NextResponse } from "next/server";

const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD ?? "";
const ADMIN_TOKEN    = process.env.ADMIN_TOKEN    ?? "";
const COOKIE_NAME    = "divai_admin";

const COOKIE_OPTS = {
  httpOnly: true,
  sameSite: "lax" as const,
  path: "/",
  // 7-day session
  maxAge: 60 * 60 * 24 * 7,
  secure: process.env.NODE_ENV === "production",
};

// POST /api/admin-auth — validate password, set cookie
export async function POST(req: NextRequest) {
  const { password } = await req.json();

  if (!ADMIN_PASSWORD || password !== ADMIN_PASSWORD) {
    return NextResponse.json({ error: "Invalid password" }, { status: 401 });
  }

  const res = NextResponse.json({ ok: true });
  res.cookies.set(COOKIE_NAME, ADMIN_TOKEN, COOKIE_OPTS);
  return res;
}

// DELETE /api/admin-auth — clear cookie (logout)
export async function DELETE() {
  const res = NextResponse.json({ ok: true });
  res.cookies.set(COOKIE_NAME, "", { ...COOKIE_OPTS, maxAge: 0 });
  return res;
}
