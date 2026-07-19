import { moneyCompact } from "../../lib/format";
import type { HorizonBand } from "../../types";

const XS = [30, 165, 300];
const CENTER_Y = 63;
const MIN_HALF = 14;
const MAX_HALF = 37;

/** Funnel showing how the P10-P90 revenue band grows with the horizon. */
export default function HorizonBandChart({ bands }: { bands: HorizonBand[] }) {
  const widths = bands.map((b) => b.revenue_p90 - b.revenue_p10);
  const maxW = Math.max(...widths);
  const halves = widths.map((w) => MIN_HALF + (w / maxW) * (MAX_HALF - MIN_HALF));

  const upper = bands.map((_, i) => `${XS[i]},${CENTER_Y - halves[i]}`);
  const lower = bands.map((_, i) => `${XS[i]},${CENTER_Y + halves[i]}`);
  const polygon = [...upper, ...[...lower].reverse()].join(" ");

  return (
    <svg viewBox="0 0 320 150" className="mt-4.5 w-full flex-1">
      <polygon points={polygon} fill="#e8560f" opacity={0.14} />
      <polyline points={upper.join(" ")} fill="none" stroke="#e8560f" strokeWidth={1.5} opacity={0.5} />
      <polyline points={lower.join(" ")} fill="none" stroke="#e8560f" strokeWidth={1.5} opacity={0.5} />
      <polyline
        points={XS.map((x) => `${x},${CENTER_Y}`).join(" ")}
        fill="none" stroke="#141b33" strokeWidth={2} strokeDasharray="4 4"
      />
      {bands.map((b, i) => (
        <g key={b.horizon_days}>
          <text x={XS[i]} y={125} fill="#5a5344" fontSize={11} fontFamily="IBM Plex Mono" textAnchor="middle">
            {b.horizon_days}d
          </text>
          <text x={XS[i]} y={143} fill="#8a8271" fontSize={10.5} fontFamily="IBM Plex Mono" textAnchor="middle">
            {moneyCompact(b.revenue_p90 - b.revenue_p10)}
          </text>
        </g>
      ))}
    </svg>
  );
}
