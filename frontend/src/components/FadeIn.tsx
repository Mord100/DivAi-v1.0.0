"use client";

/**
 * FadeIn — Scroll-triggered entrance animation.
 * Copied directly from the DiV Dynamics brand-starter kit.
 *
 * CONCEPT: Framer Motion Variants
 * ---------------------------------
 * A variant is a named animation state. You define "hidden" and "visible"
 * states, then tell Framer Motion which state to start in and which to
 * animate to. Framer handles the interpolation.
 *
 * FadeInStagger wraps multiple FadeIn children and staggers them:
 * each child starts animating 0.12s after the previous one.
 */

import { createContext, useContext } from "react";
import { motion, useReducedMotion } from "framer-motion";

const FadeInStaggerContext = createContext(false);
const viewport = { once: true, margin: "0px 0px -200px" };

export function FadeIn({ ...props }) {
  const shouldReduceMotion = useReducedMotion();
  const isInStaggerGroup = useContext(FadeInStaggerContext);

  return (
    <motion.div
      variants={{
        hidden: {
          opacity: 0,
          y: shouldReduceMotion ? 0 : 32,
          ...(isInStaggerGroup && !shouldReduceMotion ? { scale: 0.98 } : {}),
        },
        visible: {
          opacity: 1,
          y: 0,
          ...(isInStaggerGroup && !shouldReduceMotion ? { scale: 1 } : {}),
        },
      }}
      transition={{ duration: 0.55, ease: [0.25, 0.46, 0.45, 0.94] }}
      {...(isInStaggerGroup
        ? {}
        : { initial: "hidden", whileInView: "visible", viewport })}
      {...props}
    />
  );
}

export function FadeInStagger({ faster = false, ...props }: { faster?: boolean; [key: string]: unknown }) {
  return (
    <FadeInStaggerContext.Provider value={true}>
      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={viewport}
        variants={{
          hidden: {},
          visible: {
            transition: {
              staggerChildren: faster ? 0.08 : 0.12,
              delayChildren: 0.1,
            },
          },
        }}
        transition={{ duration: 0.4 }}
        {...props}
      />
    </FadeInStaggerContext.Provider>
  );
}
