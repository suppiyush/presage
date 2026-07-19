import { channelHex, shortDate } from "../../lib/format";
import type { WeeklyAnomaly, WeeklyRoasPoint } from "../../types";

const VB_W = 680;
const VB_H = 230;
const X0 = 40;
const X1 = 660;
const Y0 = 20;
const Y1 = 200;
const WEEKS_SHOWN = 12;

interface Props {
  points: WeeklyRoasPoint[];
  anomalies: WeeklyAnomaly[];
}

/** Weekly ROAS per channel over the recent window, with anomaly markers. */
export default function WeeklyRoasChart({ points, anomalies }: Props) {
  const allWeeks = [...new Set(points.map((p) => p.week_start))].sort();
  const weeks = allWeeks.slice(-WEEKS_SHOWN);
  const inWindow = points.filter((p) => weeks.includes(p.week_start));
  const channels = [...new Set(inWindow.map((p) => p.channel))].sort();

  const yMax = Math.max(...inWindow.map((p) => p.roas)) * 1.15;
  const px = (week: string) =>
    X0 + (weeks.indexOf(week) / Math.max(weeks.length - 1, 1)) * (X1 - X0);
  const py = (v: number) => Y1 - (v / yMax) * (Y1 - Y0);

  const gridValues = [yMax * 0.75, yMax * 0.45].map((v) => Math.round(v * 10) / 10);

  const flagged = anomalies.filter((a) => weeks.includes(a.week_start));

  return (
    <svg viewBox={`0 0 ${VB_W} ${VB_H}`} className="mt-4 w-full">
      <line x1={X0} y1={Y1} x2={X1} y2={Y1} stroke="#d9d1c0" />
      {gridValues.map((v) => (
        <g key={v}>
          <line x1={X0} y1={py(v)} x2={X1} y2={py(v)} stroke="#efe8da" />
          <text x={X0 - 10} y={py(v) + 4} fill="#8a8271" fontSize={11} fontFamily="IBM Plex Mono" textAnchor="end">
            {v.toFixed(1)}x
          </text>
        </g>
      ))}
      {channels.map((ch) => {
        const series = inWindow
          .filter((p) => p.channel === ch)
          .sort((a, b) => a.week_start.localeCompare(b.week_start));
        return (
          <polyline
            key={ch}
            points={series.map((p) => `${px(p.week_start)},${py(p.roas)}`).join(" ")}
            fill="none"
            stroke={channelHex(ch)}
            strokeWidth={2}
          />
        );
      })}
      {flagged.map((a, i) => (
        <circle
          key={i}
          cx={px(a.week_start)}
          cy={py(a.actual_roas)}
          r={4}
          fill="none"
          stroke={a.direction === "below" ? "#e8560f" : "#1a8f4d"}
          strokeWidth={1.5}
        />
      ))}
      {[weeks[0], weeks[Math.floor((weeks.length - 1) / 2)], weeks[weeks.length - 1]].map(
        (w, i) => (
          <text
            key={w}
            x={i === 0 ? X0 : i === 1 ? (X0 + X1) / 2 : X1}
            y={222}
            fill="#5a5344"
            fontSize={11}
            fontFamily="IBM Plex Mono"
            textAnchor={i === 0 ? "start" : i === 1 ? "middle" : "end"}
          >
            {shortDate(w)}
          </text>
        ),
      )}
    </svg>
  );
}
