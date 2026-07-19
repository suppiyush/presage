import { metric, metricLabel, metricSub, metricValue } from "../lib/tw";

interface Props {
  label: string;
  value: string;
  sub?: string;
  highlight?: boolean;
  accentValue?: boolean;
}

export default function MetricCard({ label, value, sub, highlight, accentValue }: Props) {
  return (
    <div className={`${metric} ${highlight ? "border-flame/40" : ""}`}>
      <div className={metricLabel}>{label}</div>
      <div className={`${metricValue} ${accentValue ? "text-flame" : ""}`}>{value}</div>
      {sub && <div className={metricSub}>{sub}</div>}
    </div>
  );
}
