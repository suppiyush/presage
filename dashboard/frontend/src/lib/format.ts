/** Number formatting shared across the dashboard. */

export const money = (n: number): string =>
  "$" + Math.round(n).toLocaleString("en-US");

/** Compact money for chart labels: $67k, $1.4M. */
export function moneyCompact(n: number): string {
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `$${(n / 1_000_000).toFixed(1).replace(/\.0$/, "")}M`;
  if (abs >= 1_000) return `$${Math.round(n / 1_000)}k`;
  return money(n);
}

export const roas = (n: number): string => `${n.toFixed(2)}x`;

export const pct = (n: number, digits = 1): string =>
  `${n > 0 ? "+" : ""}${n.toFixed(digits)}%`;

export const rangeCompact = (lo: number, hi: number): string =>
  `${moneyCompact(lo)}–${moneyCompact(hi)}`;

/** "2026-06-01" -> "Jun 1" */
export function shortDate(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

/** "2026-06-01" -> "Jun 1, 2026" */
export function longDate(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export const CHANNEL_COLORS: Record<string, string> = {
  google: "var(--color-google)",
  meta: "var(--color-metac)",
  microsoft: "var(--color-microsoft)",
};

export const CHANNEL_HEX: Record<string, string> = {
  google: "#2b49c4",
  meta: "#7a4fc0",
  microsoft: "#0f8f6b",
};

export const CHANNEL_LABELS: Record<string, string> = {
  google: "Google Ads",
  meta: "Meta Ads",
  microsoft: "Microsoft Ads",
};

export const channelColor = (ch: string): string => CHANNEL_COLORS[ch] ?? "var(--accent)";
export const channelHex = (ch: string): string => CHANNEL_HEX[ch] ?? "#e8560f";
export const channelLabel = (ch: string): string =>
  CHANNEL_LABELS[ch] ?? ch.charAt(0).toUpperCase() + ch.slice(1);
export const channelShort = (ch: string): string =>
  ch.charAt(0).toUpperCase() + ch.slice(1);
