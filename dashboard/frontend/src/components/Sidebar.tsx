import { channelColor, channelLabel, money, moneyCompact } from "../lib/format";
import { sideLabel } from "../lib/tw";
import type { Budgets, Meta } from "../types";

const SLIDER_MIN_MULT = 0.5;
const SLIDER_MAX_MULT = 2.0;

interface Props {
  open: boolean;
  meta: Meta | null;
  horizon: number;
  budgets: Budgets;
  onHorizonChange: (h: number) => void;
  onBudgetChange: (channel: string, value: number) => void;
}

export default function Sidebar({ open, meta, horizon, budgets, onHorizonChange, onBudgetChange }: Props) {
  const defaults = meta?.default_plans[String(horizon)] ?? {};
  const total = Object.values(budgets).reduce((a, b) => a + b, 0);

  return (
    <aside
      className={`min-w-0 flex-none overflow-hidden bg-dside py-6 transition-[width,padding] duration-200 ease-out ${
        open ? "w-[272px] border-r border-dline px-5" : "w-0 px-0"
      }`}
    >
      <div className="flex w-[232px] flex-none flex-col gap-7">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-[7px] bg-flame text-sm font-bold text-dbg">
            P
          </div>
          <div>
            <div className="text-[15px] font-semibold tracking-[-0.01em]">Presage</div>
            <div className="text-[11px] text-dmuted">Forecasting</div>
          </div>
        </div>

        <div className="flex flex-col gap-2.5">
          <div className={sideLabel}>Forecast horizon</div>
          <div className="flex gap-1 rounded-lg border border-dcardline bg-dbg p-[3px]">
            {(meta?.horizons ?? [30, 60, 90]).map((h) => (
              <button
                key={h}
                className={`flex-1 cursor-pointer rounded-md border-0 py-1.5 text-xs ${
                  h === horizon
                    ? "bg-dcardline font-semibold text-dtext"
                    : "bg-transparent font-medium text-dtext2"
                }`}
                onClick={() => onHorizonChange(h)}
              >
                {h === horizon ? `${h} days` : h}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-5">
          <div className={sideLabel}>Channel budgets · {horizon} days</div>
          {Object.keys(defaults).map((ch) => {
            const base = defaults[ch];
            const min = Math.round(base * SLIDER_MIN_MULT);
            const max = Math.round(base * SLIDER_MAX_MULT);
            const value = Math.round(budgets[ch] ?? base);
            return (
              <div className="flex flex-col gap-2" key={ch}>
                <div className="flex items-baseline justify-between">
                  <span className="flex items-center gap-[7px] text-[13px] font-medium">
                    <span
                      className="h-2 w-2 rounded-sm"
                      style={{ background: channelColor(ch) }}
                    />
                    {channelLabel(ch)}
                  </span>
                  <span className="font-mono text-[13px] font-semibold">{money(value)}</span>
                </div>
                <input
                  type="range"
                  className="w-full"
                  min={min}
                  max={max}
                  value={value}
                  step={Math.max(Math.round(base * 0.05), 1)}
                  style={{ accentColor: channelColor(ch) } as React.CSSProperties}
                  onChange={(e) => onBudgetChange(ch, Number(e.target.value))}
                />
                <div className="flex justify-between font-mono text-[11px] text-dmuted">
                  <span>{moneyCompact(min)}</span>
                  <span>{moneyCompact(max)}</span>
                </div>
              </div>
            );
          })}
          <div className="flex items-baseline justify-between border-t border-dline pt-3.5">
            <span className="text-xs text-dtext2">Total budget</span>
            <span className="font-mono text-sm font-semibold">{money(total)}</span>
          </div>
          <p className="text-[11.5px] leading-normal text-dmuted">
            Defaults reflect each channel's spend pacing over the last four weeks.
            Move a slider to re-run the forecast.
          </p>
        </div>
      </div>
    </aside>
  );
}
