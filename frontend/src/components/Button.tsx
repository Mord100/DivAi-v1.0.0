"use client";

/**
 * Button — Pill-shaped button component.
 * Adapted from the DiV Dynamics brand-starter kit.
 *
 * Two variants:
 *   default: dark (Ink) background, white text
 *   invert:  white background, dark text (for use on dark backgrounds)
 */

import Link from "next/link";
import clsx from "clsx";
import { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  invert?: boolean;
  href?: string;
  className?: string;
  children: React.ReactNode;
}

export function Button({ invert, href, className, children, ...props }: ButtonProps) {
  const cls = clsx(
    className,
    "inline-flex items-center rounded-full px-4 py-1.5 text-sm font-semibold transition",
    invert
      ? "bg-white text-neutral-950 hover:bg-neutral-200"
      : "bg-neutral-950 text-white hover:bg-neutral-800"
  );

  if (href) {
    return (
      <Link href={href} className={cls}>
        <span>{children}</span>
      </Link>
    );
  }

  return (
    <button className={cls} {...props}>
      <span>{children}</span>
    </button>
  );
}
