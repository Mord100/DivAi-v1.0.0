import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/supabase/AuthProvider";

export const metadata: Metadata = {
  title: "DivAi — AI-Powered Lead Intelligence",
  description:
    "Turn any website into a qualified software lead with a full technical proposal in under 5 minutes.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="bg-white antialiased">
      <body className="font-sans text-neutral-950">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
