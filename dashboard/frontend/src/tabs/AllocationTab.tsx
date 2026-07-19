import MetricCard from "../components/MetricCard";
import { useCachedFetch } from "../hooks/useCachedFetch";
import { budgetKey, postAllocation } from "../lib/api";
import { channelColor, channelLabel, money, pct } from "../lib/format";
import { card, cardTitle, skeleton, table, tdNum, tdTxt, th, thNum } from "../lib/tw";
import type { Budgets } from "../types";

export default function AllocationTab({ horizon, budgets }: { horizon: number; budgets: Budgets }) {
  const { data, error } = useCachedFetch(
    `allocation-${horizon}-${budgetKey(budgets)}`,
    () => postAllocation(horizon, budgets),
  );

  if (error) return <div className={card}>Could not load the allocation: {error}</div>;
  if (!data) {
    return (
      <>
        <div className="grid grid-cols-3 gap-4">
          {[0, 1, 2].map((i) => <div key={i} className={skeleton} style={{ height: 104 }} />)}
        </div>
        <div className={skeleton} style={{ height: 260 }} />
      </>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-3 gap-4">
        <MetricCard label="Revenue at current split" value={money(data.current_revenue_p50)} />
        <MetricCard label="Revenue at suggested split" value={money(data.optimal_revenue_p50)} />
        <MetricCard
          label="Difference · same total spend"
          value={`+${money(data.lift_abs)}`}
          sub={`${pct(data.lift_pct)} projected revenue`}
          highlight
          accentValue
        />
      </div>

      <div className={card}>
        <div className={`${cardTitle} mb-3.5`}>Current vs. suggested budget</div>
        <table className={table}>
          <thead>
            <tr>
              <th className={th}>Channel</th>
              <th className={thNum}>Current budget</th>
              <th className={thNum}>Suggested budget</th>
              <th className={thNum}>Change</th>
              <th className={th}>Rationale</th>
            </tr>
          </thead>
          <tbody>
            {data.channels.map((c) => (
              <tr key={c.channel}>
                <td className={tdTxt}>
                  <span className="flex items-center gap-2">
                    <span
                      className="h-2 w-2 rounded-sm"
                      style={{ background: channelColor(c.channel) }}
                    />
                    {channelLabel(c.channel)}
                  </span>
                </td>
                <td className={tdNum}>{money(c.current)}</td>
                <td className={tdNum}>{money(c.suggested)}</td>
                <td className={`${tdNum} ${c.change_pct >= 0 ? "text-pos" : "text-neg"}`}>
                  {pct(c.change_pct, 0)}{c.at_guardrail ? " (capped)" : ""}
                </td>
                <td className={`${tdTxt} text-xs text-dtext2`}>{c.rationale}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className={`${card} px-6 py-4.5`}>
        <div className="mb-1.5 text-[13px] font-semibold">About the ±40% guardrails</div>
        <p className="m-0 max-w-[900px] text-[12.5px] leading-relaxed text-dtext2">
          Suggested changes are capped at ±40% of each channel's current budget.
          Response curves are only reliable near spend levels we have actually
          observed, and abrupt budget swings destabilize platform bidding
          algorithms. A {pct(data.lift_pct)} lift may look modest — but it comes
          from the same total spend, compounds monthly, and carries no additional
          risk. Small, repeatable reallocations are how this tool is meant to be
          used.
        </p>
      </div>
    </div>
  );
}
