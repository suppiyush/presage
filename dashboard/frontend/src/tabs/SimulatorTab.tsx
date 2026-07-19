import CurveChart from "../components/charts/CurveChart";
import { useCachedFetch } from "../hooks/useCachedFetch";
import { budgetKey, postCurves } from "../lib/api";
import { channelColor, channelLabel, moneyCompact, roas } from "../lib/format";
import { card, cardSub, cardTitle, skeleton } from "../lib/tw";
import type { Budgets, ChannelCurve } from "../types";

/** Marginal return per extra dollar from current budget to 2x — for the notes. */
function curveNotes(curves: ChannelCurve[]) {
  const marginal = curves.map((c) => {
    const at1 = c.points.reduce((b, p) =>
      Math.abs(p.budget_multiplier - 1) < Math.abs(b.budget_multiplier - 1) ? p : b);
    const at2 = c.points[c.points.length - 1];
    const extraSpend = at2.spend - at1.spend;
    return {
      channel: c.channel,
      marginalRoas: extraSpend > 0 ? (at2.revenue_p50 - at1.revenue_p50) / extraSpend : 0,
      roas2x: at2.roas_p50,
    };
  });
  const best = marginal.reduce((a, b) => (a.marginalRoas > b.marginalRoas ? a : b));
  const worst = marginal.reduce((a, b) => (a.marginalRoas < b.marginalRoas ? a : b));
  return { best, worst };
}

export default function SimulatorTab({ horizon, budgets }: { horizon: number; budgets: Budgets }) {
  const { data, error } = useCachedFetch(
    `curves-${horizon}-${budgetKey(budgets)}`,
    () => postCurves(horizon, budgets),
  );

  if (error) return <div className={card}>Could not load response curves: {error}</div>;
  if (!data) {
    return (
      <div className="grid grid-cols-2 gap-4">
        <div className={skeleton} style={{ height: 380 }} />
        <div className={skeleton} style={{ height: 380 }} />
      </div>
    );
  }

  const { best, worst } = curveNotes(data.curves);

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className={card}>
        <div className={cardTitle}>Revenue response curves</div>
        <div className={cardSub}>
          Projected {horizon}-day revenue as spend scales · dot marks current budget
        </div>
        <CurveChart
          curves={data.curves}
          yKey="revenue_p50"
          fmt={moneyCompact}
          labelMode="dot"
          xTickLabels={["0.5x", "current", "2.0x spend"]}
        />
        <p className="mt-3 text-xs leading-normal text-dtext2">
          {channelLabel(best.channel)} has the most headroom past its current
          budget. {channelLabel(worst.channel)}'s curve flattens early — extra
          spend buys little revenue.
        </p>
      </div>
      <div className={card}>
        <div className={cardTitle}>ROAS vs. budget multiplier</div>
        <div className={cardSub}>Diminishing returns as budgets scale from 0.5x to 2.0x</div>
        <CurveChart
          curves={data.curves}
          yKey="roas_p50"
          fmt={roas}
          labelMode="ends"
          dashAtCurrent
          xTickLabels={["0.5x", "1.0x (current)", "2.0x"]}
        />
        <p className="mt-3 text-xs leading-normal text-dtext2">
          Every channel loses efficiency as budget grows. At double budget,{" "}
          {channelLabel(worst.channel)}'s ROAS is {roas(worst.roas2x)}.
        </p>
      </div>
      <div className={`${card} col-span-full flex items-center gap-6 px-5 py-3.5 text-[12.5px] text-dtext2`}>
        {data.curves.map((c) => (
          <span className="flex items-center gap-1.5" key={c.channel}>
            <span
              className="h-[3px] w-4 rounded-sm"
              style={{ background: channelColor(c.channel) }}
            />
            {channelLabel(c.channel)}
          </span>
        ))}
        <span className="ml-auto">
          Curves come from the trained model with spend as an input feature.
        </span>
      </div>
    </div>
  );
}
