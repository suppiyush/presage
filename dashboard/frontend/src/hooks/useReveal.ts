import { useEffect } from "react";

/** Staggered scroll-reveal: observes every [data-reveal] element under the
 *  page and adds .revealed when it enters the viewport (once). Elements set
 *  their stagger via style={{ "--reveal-delay": "120ms" }}. */
export function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll("[data-reveal]");
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("revealed");
            io.unobserve(entry.target);
          }
        }
      },
      { threshold: 0.15 },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);
}

/** Helper for inline stagger delays. */
export const revealDelay = (ms: number) =>
  ({ "--reveal-delay": `${ms}ms` }) as React.CSSProperties;
