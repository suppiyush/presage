import { revealDelay } from "../../hooks/useReveal";

const STEPS = [
  {
    num: "01", color: "#2b49c4", title: "Forecast",
    body: "Projected revenue and ROAS per channel over 30, 60 or 90 days — always with a P10–P90 range.",
  },
  {
    num: "02", color: "#5a4bc2", title: "Simulate",
    body: "Response curves show what each extra dollar buys, and where diminishing returns set in.",
  },
  {
    num: "03", color: "#a850a0", title: "Reallocate",
    body: "A suggested split within ±40% guardrails — small, safe shifts that compound month over month.",
  },
  {
    num: "04", color: "#e8560f", title: "Catch risk",
    body: "Anomaly detection flags ROAS shifts early — like a 60% Microsoft decline — before they burn budget.",
  },
];

export default function HowItWorks() {
  return (
    <section id="how" className="border-t border-sand px-10 py-18">
      <div className="mx-auto max-w-[1080px]">
        <div data-reveal className="font-mono text-[12.5px] font-medium uppercase tracking-[0.1em] text-flame">
          How it works
        </div>
        <h2
          data-reveal
          style={revealDelay(90)}
          className="mt-3 max-w-[560px] text-[34px] font-bold tracking-[-0.02em] text-ink"
        >
          From raw spend data to a decision in four steps
        </h2>
        <div className="mt-11 grid grid-cols-4 gap-5">
          {STEPS.map((s, i) => (
            <div
              key={s.num}
              data-reveal
              style={revealDelay(i * 110)}
              className="rounded-xl border border-sand bg-paper p-6 transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_12px_32px_rgba(20,27,51,0.10)]"
            >
              <div className="font-mono text-[13px] font-semibold" style={{ color: s.color }}>
                {s.num}
              </div>
              <div className="mt-3 text-base font-semibold text-ink">{s.title}</div>
              <p className="mt-2 text-[13.5px] leading-relaxed text-clay">{s.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
