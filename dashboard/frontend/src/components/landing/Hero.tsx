import { Link } from "react-router-dom";
import { revealDelay } from "../../hooks/useReveal";

const STATS = [
  { big: "80%", small: "of real outcomes land inside our P10–P90 range, back-tested on 18 months" },
  { big: "3", small: "channels forecast together — Google, Meta and Microsoft Ads" },
  { big: "±40%", small: "guardrails on every budget suggestion, so reallocations stay safe" },
];

export default function Hero() {
  return (
    <section
      id="product"
      className="px-10 pb-18 pt-22 text-center"
      style={{ background: "radial-gradient(ellipse 900px 420px at 50% -80px,#f3ecdd,#faf6ef 70%)" }}
    >
      <div
        data-reveal
        className="inline-flex items-center gap-2 rounded-[20px] border border-sand2 bg-paper px-3.5 py-1.5 text-[12.5px] font-medium text-clay"
      >
        <span
          className="h-[7px] w-[7px] rounded-full"
          style={{ background: "linear-gradient(90deg,#2b49c4,#e8560f)" }}
        />
        Forecasting for Google, Meta and Microsoft Ads
      </div>
      <h1
        data-reveal
        style={revealDelay(90)}
        className="mx-auto mt-6.5 max-w-[760px] text-[56px] font-bold leading-[1.08] tracking-[-0.03em] text-ink"
      >
        Know what your ad spend will return —{" "}
        <span
          className="bg-clip-text text-transparent"
          style={{ backgroundImage: "linear-gradient(90deg,#2b49c4 10%,#7a4fc0 50%,#e8560f 90%)" }}
        >
          before you spend it
        </span>
      </h1>
      <p
        data-reveal
        style={revealDelay(180)}
        className="mx-auto mt-5.5 max-w-[560px] text-lg leading-relaxed text-clay"
      >
        Presage forecasts revenue and ROAS across your three ad channels, with
        honest uncertainty ranges and budget suggestions that stay inside safe
        guardrails.
      </p>
      <div data-reveal style={revealDelay(270)} className="mt-8.5 flex justify-center gap-3.5">
        <Link
          to="/dashboard"
          className="rounded-[10px] bg-ink px-7 py-3.5 text-[15px] font-semibold text-paper transition-all duration-200 hover:-translate-y-0.5 hover:bg-blue"
        >
          Try the live dashboard
        </Link>
        <a
          href="#how"
          className="rounded-[10px] border border-sand2 bg-paper px-7 py-3.5 text-[15px] font-semibold text-ink transition-all duration-200 hover:-translate-y-0.5 hover:border-ink"
        >
          See how it works
        </a>
      </div>
      <div
        data-reveal
        style={revealDelay(360)}
        className="mx-auto mt-15 grid max-w-[880px] grid-cols-3 gap-px overflow-hidden rounded-[14px] border border-sand bg-sand"
      >
        {STATS.map((s) => (
          <div key={s.big} className="bg-paper px-5.5 py-6.5 text-left">
            <div className="font-mono text-3xl font-semibold tracking-[-0.02em] text-ink">
              {s.big}
            </div>
            <div className="mt-1.5 text-[13.5px] leading-normal text-clay">{s.small}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
