import { useLayoutEffect, useRef, useState } from "react";

export type TabKey = "forecast" | "simulator" | "allocation" | "anomalies" | "summary";

const TABS: { key: TabKey; label: string }[] = [
  { key: "forecast", label: "Forecast" },
  { key: "simulator", label: "Budget simulator" },
  { key: "allocation", label: "Suggested allocation" },
  { key: "anomalies", label: "Anomalies & risk" },
  { key: "summary", label: "Written summary" },
];

interface Props {
  active: TabKey;
  onChange: (key: TabKey) => void;
}

/** Centered pill tab bar with a sliding active indicator (Sarvam-style). */
export default function TabNav({ active, onChange }: Props) {
  const btnRefs = useRef<Partial<Record<TabKey, HTMLButtonElement | null>>>({});
  const [indicator, setIndicator] = useState({ left: 0, width: 0, ready: false });

  useLayoutEffect(() => {
    const measure = () => {
      const el = btnRefs.current[active];
      if (el) setIndicator({ left: el.offsetLeft, width: el.offsetWidth, ready: true });
    };
    measure();
    window.addEventListener("resize", measure);
    // re-measure once fonts have loaded (label widths shift slightly)
    document.fonts?.ready.then(measure);
    return () => window.removeEventListener("resize", measure);
  }, [active]);

  return (
    <div className="mt-4 flex justify-center px-8">
      <nav className="relative flex w-fit gap-1 rounded-full border border-dline bg-[#f3ecdd] p-1">
        {indicator.ready && (
          <span
            aria-hidden
            className="absolute bottom-1 top-1 rounded-full bg-dtext transition-[left,width] duration-300 ease-[cubic-bezier(0.22,0.61,0.36,1)] motion-reduce:transition-none"
            style={{ left: indicator.left, width: indicator.width }}
          />
        )}
        {TABS.map((t) => (
          <button
            key={t.key}
            ref={(el) => (btnRefs.current[t.key] = el)}
            className={`relative z-10 cursor-pointer rounded-full border-0 bg-transparent px-4.5 py-2.5 text-[13px] transition-colors duration-200 ${
              t.key === active
                ? "font-semibold text-dcard"
                : "font-medium text-dtext2 hover:text-dtext"
            }`}
            onClick={() => onChange(t.key)}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
