import MetricCard from "../components/MetricCard";
import ChannelBars from "../components/charts/ChannelBars";
import HorizonBandChart from "../components/charts/HorizonBandChart";
import { channelColor, channelShort, money, pct, rangeCompact, roas } from "../lib/format";
import { card, cardSub, cardTitle, skeleton, table, tdNum, tdTxt, th, thNum } from "../lib/tw";
import type { Forecast, Meta } from "../types";

interface Props {
  meta: Meta | null;
  forecast: Forecast | null;
  loading: boolean;
  horizon: number;
}

export default function ForecastTab({ meta, forecast, loading, horizon }: Props) {
  if (!forecast || !meta) {
    return (
      <>
        <div className="grid grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => <div key={i} className={skeleton} style={{ height: 104 }} />)}
        </div>
        <div className={skeleton} style={{ height: 360 }} />
        <div className={skeleton} style={{ height: 300 }} />
      </>
    );
  }

  const t = forecast.totals;
  const coverage = Math.round(meta.calibration.inside * 100);

  return (
    <div className={`flex flex-col gap-6 ${loading ? "opacity-60" : ""}`}>
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          label={`Projected revenue · ${horizon} days`}
          value={money(t.revenue_p50)}
          sub={`${pct(t.vs_recent_pace_pct)} vs. recent ${horizon}-day pace`}
        />
        <MetricCard
          label="P10–P90 range"
          value={rangeCompact(t.revenue_p10, t.revenue_p90)}
          sub="80% of outcomes expected inside"
        />
        <MetricCard
          label="Blended ROAS · forecast"
          value={roas(t.roas_p50)}
          sub="Across all three channels"
        />
        <MetricCard
          label="Actual ROAS · last 4 weeks"
          value={roas(t.trailing_roas)}
          sub={`Forecast sits ${Math.abs(t.roas_vs_trailing_pct).toFixed(1)}% ${t.roas_vs_trailing_pct < 0 ? "below" : "above"} actuals`}
        />
      </div>

      <div className="grid grid-cols-[1fr_380px] gap-4">
        <div className={card}>
          <div className="flex items-baseline justify-between">
            <div className={cardTitle}>Revenue forecast by channel</div>
            <div className="text-[11.5px] text-dmuted">Whiskers show P10–P90</div>
          </div>
          <ChannelBars channels={forecast.by_channel} />
        </div>
        <div className={`${card} flex flex-col`}>
          <div className={cardTitle}>Uncertainty over longer horizons</div>
          <div className={cardSub}>P10–P90 revenue range at each horizon</div>
          <HorizonBandChart bands={meta.horizon_bands} />
          <p className="mt-3.5 text-[11.5px] leading-normal text-dtext2">
            Ranges are back-tested: {coverage}% of actual outcomes landed inside
            the stated P10–P90 band.
          </p>
        </div>
      </div>

      <div className={card}>
        <div className={`${cardTitle} mb-3.5`}>Forecast by campaign type</div>
        <table className={table}>
          <thead>
            <tr>
              <th className={th}>Campaign type</th>
              <th className={th}>Channel</th>
              <th className={thNum}>Budget</th>
              <th className={thNum}>Forecast revenue</th>
              <th className={thNum}>P10–P90</th>
              <th className={thNum}>ROAS</th>
            </tr>
          </thead>
          <tbody>
            {forecast.groups.map((g) => (
              <tr key={`${g.channel}-${g.campaign_type}`}>
                <td className={tdTxt}>{g.campaign_type}</td>
                <td className={tdTxt} style={{ color: channelColor(g.channel) }}>
                  {channelShort(g.channel)}
                </td>
                <td className={tdNum}>{money(g.spend)}</td>
                <td className={tdNum}>{money(g.revenue_p50)}</td>
                <td className={`${tdNum} text-dtext2`}>
                  {rangeCompact(g.revenue_p10, g.revenue_p90)}
                </td>
                <td className={tdNum}>{roas(g.roas_p50)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
