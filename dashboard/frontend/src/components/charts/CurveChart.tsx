import { channelHex } from "../../lib/format";
import type { ChannelCurve } from "../../types";

const VB_W = 680;
const VB_H = 280;
const X0 = 40;
const X1 = 660;
const Y0 = 20;
const Y1 = 240;
const LABEL_MIN_GAP = 16;

interface Props {
  curves: ChannelCurve[];
  yKey: "revenue_p50" | "roas_p50";
  fmt: (v: number) => string;
  /** "dot": marker + label at multiplier 1.0. "ends": labels at both curve ends. */
  labelMode: "dot" | "ends";
  dashAtCurrent?: boolean;
  xTickLabels: [string, string, string];
}

interface LabelSpec {
  x: number;
  y: number;
  text: string;
  color: string;
  anchor?: "start" | "end";
}

/** Push overlapping labels apart vertically (they stay near their point). */
function resolveCollisions(labels: LabelSpec[]): LabelSpec[] {
  const sorted = [...labels].sort((a, b) => a.y - b.y);
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i].y - sorted[i - 1].y < LABEL_MIN_GAP) {
      sorted[i].y = sorted[i - 1].y + LABEL_MIN_GAP;
    }
  }
  return sorted;
}

export default function CurveChart({ curves, yKey, fmt, labelMode, dashAtCurrent, xTickLabels }: Props) {
  const multipliers = curves[0]?.points.map((p) => p.budget_multiplier) ?? [];
  const xMin = Math.min(...multipliers);
  const xMax = Math.max(...multipliers);
  const yMax = Math.max(...curves.flatMap((c) => c.points.map((p) => p[yKey]))) * 1.12;

  const px = (m: number) => X0 + ((m - xMin) / (xMax - xMin)) * (X1 - X0);
  const py = (v: number) => Y1 - (v / yMax) * (Y1 - Y0);
  const currentX = px(1.0);

  const labels: LabelSpec[] = [];
  for (const c of curves) {
    const color = channelHex(c.channel);
    if (labelMode === "dot") {
      const at = c.points.reduce((best, p) =>
        Math.abs(p.budget_multiplier - 1) < Math.abs(best.budget_multiplier - 1) ? p : best);
      labels.push({ x: px(at.budget_multiplier) + 12, y: py(at[yKey]) + 4, text: fmt(at[yKey]), color });
    } else {
      const first = c.points[0];
      const last = c.points[c.points.length - 1];
      labels.push({ x: px(first.budget_multiplier) + 6, y: py(first[yKey]) - 7, text: fmt(first[yKey]), color });
      labels.push({ x: px(last.budget_multiplier) - 4, y: py(last[yKey]) - 7, text: fmt(last[yKey]), color, anchor: "end" });
    }
  }

  return (
    <svg viewBox={`0 0 ${VB_W} ${VB_H}`} className="mt-4 w-full">
      <line x1={X0} y1={Y0} x2={X0} y2={Y1} stroke="#d9d1c0" />
      <line x1={X0} y1={Y1} x2={X1} y2={Y1} stroke="#d9d1c0" />
      {dashAtCurrent && (
        <line x1={currentX} y1={Y0} x2={currentX} y2={Y1} stroke="#d9d1c0" strokeDasharray="3 5" />
      )}
      {curves.map((c) => (
        <path
          key={c.channel}
          d={c.points
            .map((p, i) => `${i === 0 ? "M" : "L"}${px(p.budget_multiplier)},${py(p[yKey])}`)
            .join(" ")}
          fill="none"
          stroke={channelHex(c.channel)}
          strokeWidth={2.5}
        />
      ))}
      {labelMode === "dot" &&
        curves.map((c) => {
          const at = c.points.reduce((best, p) =>
            Math.abs(p.budget_multiplier - 1) < Math.abs(best.budget_multiplier - 1) ? p : best);
          return (
            <circle
              key={c.channel}
              cx={px(at.budget_multiplier)}
              cy={py(at[yKey])}
              r={5}
              fill={channelHex(c.channel)}
              stroke="#faf6ef"
              strokeWidth={2}
            />
          );
        })}
      {resolveCollisions(labels).map((l, i) => (
        <text
          key={i}
          x={l.x}
          y={l.y}
          fill={labelMode === "dot" ? "#141b33" : l.color}
          fontSize={12}
          fontFamily="IBM Plex Mono"
          textAnchor={l.anchor ?? "start"}
        >
          {l.text}
        </text>
      ))}
      <text x={X0} y={260} fill="#5a5344" fontSize={11} fontFamily="IBM Plex Mono">
        {xTickLabels[0]}
      </text>
      <text x={currentX} y={260} fill="#5a5344" fontSize={11} fontFamily="IBM Plex Mono" textAnchor="middle">
        {xTickLabels[1]}
      </text>
      <text x={X1} y={260} fill="#5a5344" fontSize={11} fontFamily="IBM Plex Mono" textAnchor="end">
        {xTickLabels[2]}
      </text>
    </svg>
  );
}
