import { useEffect, useRef, useState } from "react";
import { postNarrative } from "../lib/api";
import { btnGhost, btnPrimary, card } from "../lib/tw";
import type { Budgets, Narrative } from "../types";

const STAGES = [
  "Reading the current forecast…",
  "Comparing channel trends…",
  "Checking anomalies and guardrails…",
  "Drafting the summary…",
];
const STAGE_INTERVAL_MS = 2500;

type Phase = "idle" | "loading" | "done" | "error";

export default function SummaryTab({ horizon, budgets }: { horizon: number; budgets: Budgets }) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [stage, setStage] = useState(STAGES[0]);
  const [result, setResult] = useState<Narrative | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timers = useRef<number[]>([]);

  useEffect(() => () => timers.current.forEach(window.clearTimeout), []);

  const generate = () => {
    timers.current.forEach(window.clearTimeout);
    setPhase("loading");
    setStage(STAGES[0]);
    timers.current = STAGES.slice(1).map((s, i) =>
      window.setTimeout(() => setStage(s), (i + 1) * STAGE_INTERVAL_MS),
    );
    postNarrative(horizon, budgets)
      .then((n) => {
        setResult(n);
        setPhase("done");
      })
      .catch((e) => {
        setError(String(e));
        setPhase("error");
      })
      .finally(() => timers.current.forEach(window.clearTimeout));
  };

  return (
    <div className="flex max-w-[820px] flex-col gap-5">
      <div className={`${card} px-7 py-6`}>
        <div className="text-[15px] font-semibold">Plain-language summary</div>
        <p className="mt-1.5 text-[12.5px] leading-relaxed text-dtext2">
          Generates a written recap of the current forecast, budget suggestions,
          and risks — suitable for pasting into an email or weekly report. Takes
          about ten seconds.
        </p>
        <div className="mt-4.5 flex items-center gap-3.5">
          {phase === "loading" ? (
            <>
              <button className={btnPrimary} disabled>Working…</button>
              <span className="flex items-center gap-2.5 text-[12.5px] text-dtext2">
                <span className="animate-pulse-fast h-2 w-2 rounded-full bg-flame" />
                {stage}
              </span>
            </>
          ) : phase === "done" ? (
            <button className={btnGhost} onClick={generate}>Regenerate</button>
          ) : (
            <button className={btnPrimary} onClick={generate}>Generate summary</button>
          )}
          {phase === "error" && (
            <span className="text-[12.5px] text-neg">Generation failed: {error}</span>
          )}
        </div>
      </div>

      {phase === "done" && result && (
        <div className={`${card} px-7 py-6`}>
          <p className="m-0 whitespace-pre-line text-[13.5px] leading-[1.75] text-dbody">
            {result.text}
          </p>
          <div className="mt-4.5 flex justify-between border-t border-dline pt-3.5 text-[11.5px] text-dmuted">
            <span>Provider: {result.provider}</span>
            <span className="font-mono">Generated {result.generated_at}</span>
          </div>
        </div>
      )}
    </div>
  );
}
