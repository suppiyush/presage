import { channelColor, channelShort, moneyCompact, rangeCompact } from "../../lib/format";
import type { ChannelForecast } from "../../types";

const PLOT_HEIGHT = 250;

/** Bar chart with P10-P90 whisker per channel, scaled to the tallest P90. */
export default function ChannelBars({ channels }: { channels: ChannelForecast[] }) {
  const scale = Math.max(...channels.map((c) => c.revenue_p90)) * 1.15;
  const pctOf = (v: number) => (v / scale) * 100;

  return (
    <>
      <div
        className="mt-6 flex items-end gap-14 border-b border-dstrong px-8"
        style={{ height: PLOT_HEIGHT }}
      >
        {channels.map((c) => (
          <div key={c.channel} className="relative h-full flex-1">
            <div
              className="absolute bottom-0 left-1/2 w-16 -translate-x-1/2 rounded-t-[5px] opacity-90"
              style={{ height: `${pctOf(c.revenue_p50)}%`, background: channelColor(c.channel) }}
            />
            {/* whisker: vertical line P10 -> P90 with caps */}
            <div
              className="absolute left-1/2 w-0.5 -translate-x-1/2 bg-dtext"
              style={{
                bottom: `${pctOf(c.revenue_p10)}%`,
                height: `${pctOf(c.revenue_p90) - pctOf(c.revenue_p10)}%`,
              }}
            />
            {[c.revenue_p10, c.revenue_p90].map((v, i) => (
              <div
                key={i}
                className="absolute left-1/2 h-0.5 w-3.5 -translate-x-1/2 bg-dtext"
                style={{ bottom: `${pctOf(v)}%` }}
              />
            ))}
            <div
              className="absolute left-1/2 -translate-x-1/2 whitespace-nowrap font-mono text-[13px] font-semibold"
              style={{ bottom: `calc(${pctOf(c.revenue_p90)}% + 8px)` }}
            >
              {moneyCompact(c.revenue_p50)}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-2.5 flex gap-14 px-8">
        {channels.map((c) => (
          <div key={c.channel} className="flex-1 text-center">
            <div className="text-[12.5px] font-medium">{channelShort(c.channel)}</div>
            <div className="font-mono text-[11px] text-dmuted">
              {rangeCompact(c.revenue_p10, c.revenue_p90)}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
