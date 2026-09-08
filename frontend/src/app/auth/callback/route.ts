import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

// Handles both OAuth redirects (Google) and email confirmation links.
// Supabase redirects here after the user clicks the login link / OAuth consent.
export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/history";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  // Something went wrong — redirect to login with error flag
  return NextResponse.redirect(`${origin}/login?error=auth_failed`);
}
