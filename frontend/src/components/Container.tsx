/**
 * Container — Max-width centered wrapper.
 * Every page section wraps its content in this.
 * Pattern from DiV Dynamics brand-starter kit.
 */
import clsx from "clsx";

interface ContainerProps {
  className?: string;
  children: React.ReactNode;
}

export function Container({ className, children }: ContainerProps) {
  return (
    <div className={clsx("mx-auto max-w-7xl px-6 lg:px-8", className)}>
      {children}
    </div>
  );
}
