import WeeklyRoasChart from "../components/charts/WeeklyRoasChart";
import { useCachedFetch } from "../hooks/useCachedFetch";
import { getAnomalies } from "../lib/api";
import { channelColor, channelLabel, channelShort, roas, shortDate } from "../lib/format";
import { card, cardTitle, skeleton, table, tdNum, tdTxt, th, thNum } from "../lib/tw";

export default function AnomaliesTab() {
  const { data, error } = useCachedFetch("anomalies", getAnomalies);

  if (error) return <div className={card}>Could not load anomalies: {error}</div>;
  if (!data) {
    return (
      <>
        <div className={skeleton} style={{ height: 92 }} />
        <div className="grid grid-cols-2 gap-4">
          <div className={skeleton} style={{ height: 240 }} />
          <div className={skeleton} style={{ height: 240 }} />
        </div>
      </>
    );
  }

  const worst = data.regime_shifts.length
    ? data.regime_shifts.reduce((a, b) =>
        Math.abs(a.change_pct) > Math.abs(b.change_pct) ? a : b)
    : null;
  const recentAnomalies = [...data.weekly_anomalies].reverse().slice(0, 8);

  return (
    <div className="flex flex-col gap-6">
      {worst && (
        <div className="flex items-start gap-4 rounded-[10px] border border-flame/40 bg-alertbg px-5.5 py-4.5">
          <div className="animate-pulse-soft mt-1.5 h-2.5 w-2.5 flex-none rounded-full bg-flame" />
          <div>
            <div className="text-sm font-semibold text-alerttitle">
              {channelLabel(worst.channel)} ROAS has shifted materially
            </div>
            <p className="mt-1.5 max-w-[920px] text-[12.5px] leading-relaxed text-alertbody">
              ROAS over the last four weeks averaged {roas(worst.recent_roas)}{" "}
              against a long-run {roas(worst.historical_roas)} — a{" "}
              {Math.abs(worst.change_pct).toFixed(0)}% decline sustained across the
              full window, not a single bad week. The forecast already reflects the
              lower efficiency; the suggested allocation moves budget away until
              performance recovers.
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div className={card}>
          <div className={`${cardTitle} mb-3.5`}>
            ROAS shift by channel · recent weeks vs. history
          </div>
          <table className={table}>
            <thead>
              <tr>
                <th className={th}>Channel</th>
                <th className={thNum}>Prior ROAS</th>
                <th className={thNum}>Recent ROAS</th>
                <th className={thNum}>Shift</th>
                <th className={thNum}>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.regime_shifts.map((s) => (
                <tr key={s.channel} className="bg-rowhl">
                  <td className={`${tdTxt} font-semibold`} style={{ color: channelColor(s.channel) }}>
                    {channelShort(s.channel)}
                  </td>
                  <td className={tdNum}>{roas(s.historical_roas)}</td>
                  <td className={`${tdNum} font-semibold`}>{roas(s.recent_roas)}</td>
                  <td className={`${tdNum} font-semibold text-flame`}>
                    {s.change_pct.toFixed(1)}%
                  </td>
                  <td className={`${tdTxt} text-right font-semibold text-flame`}>Shifted</td>
                </tr>
              ))}
              {["google", "meta", "microsoft"]
                .filter((ch) => !data.regime_shifts.some((s) => s.channel === ch))
                .map((ch) => (
                  <tr key={ch}>
                    <td className={tdTxt} style={{ color: channelColor(ch) }}>
                      {channelShort(ch)}
                    </td>
                    <td className={`${tdNum} text-dtext2`} colSpan={2}>—</td>
                    <td className={`${tdNum} text-dtext2`}>within normal range</td>
                    <td className={`${tdTxt} text-right text-pos`}>Stable</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className={card}>
          <div className={`${cardTitle} mb-3.5`}>
            Unusual weeks · ROAS far from recent average
          </div>
          <table className={table}>
            <thead>
              <tr>
                <th className={th}>Week of</th>
                <th className={th}>Channel</th>
                <th className={thNum}>ROAS</th>
                <th className={thNum}>Expected</th>
                <th className={thNum}>Deviation</th>
              </tr>
            </thead>
            <tbody>
              {recentAnomalies.map((a, i) => (
                <tr key={i}>
                  <td className={tdNum.replace("text-right", "")}>{shortDate(a.week_start)}</td>
                  <td className={tdTxt} style={{ color: channelColor(a.channel) }}>
                    {channelShort(a.channel)}
                  </td>
                  <td className={tdNum}>{roas(a.actual_roas)}</td>
                  <td className={`${tdNum} text-dtext2`}>{roas(a.expected_roas)}</td>
                  <td className={`${tdNum} ${a.direction === "below" ? "text-flame" : "text-pos"}`}>
                    {a.direction === "below" ? "−" : "+"}{Math.abs(a.deviation_sigma).toFixed(1)}σ
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3.5 text-[11.5px] leading-normal text-dmuted">
            Weeks flagged when ROAS deviates more than 1.5σ from that channel's
            trailing average.
          </p>
        </div>
      </div>

      <div className={card}>
        <div className="flex items-baseline justify-between">
          <div className={cardTitle}>Weekly ROAS · last 12 weeks</div>
          <div className="flex gap-4 text-xs text-dtext2">
            {["google", "meta", "microsoft"].map((ch) => (
              <span className="flex items-center gap-1.5" key={ch}>
                <span
                  className="h-[3px] w-3.5 rounded-sm"
                  style={{ background: channelColor(ch) }}
                />
                {channelShort(ch)}
              </span>
            ))}
          </div>
        </div>
        <WeeklyRoasChart points={data.weekly_roas} anomalies={data.weekly_anomalies} />
      </div>
    </div>
  );
}
