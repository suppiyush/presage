import type {
  Allocation, Anomalies, Budgets, Forecast, Meta, Narrative, Simulator,
} from "../types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    throw new Error(`${init?.method ?? "GET"} ${url} failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const getMeta = () => request<Meta>("/api/meta");

export const postForecast = (horizon: number, budgets: Budgets) =>
  request<Forecast>("/api/forecast", json({ horizon, budgets }));

export const postCurves = (horizon: number, budgets: Budgets) =>
  request<Simulator>("/api/response-curves", json({ horizon, budgets }));

export const postAllocation = (horizon: number, budgets: Budgets) =>
  request<Allocation>("/api/allocation", json({ horizon, budgets }));

export const getAnomalies = () => request<Anomalies>("/api/anomalies");

export const postNarrative = (horizon: number, budgets: Budgets) =>
  request<Narrative>("/api/narrative", json({ horizon, budgets }));

/** Stable cache key for a budget scenario. */
export const budgetKey = (budgets: Budgets): string =>
  Object.keys(budgets)
    .sort()
    .map((ch) => `${ch}:${Math.round(budgets[ch])}`)
    .join(",");

export function exportCsvUrl(horizon: number, budgets: Budgets): string {
  const params = new URLSearchParams({ horizon: String(horizon) });
  for (const [ch, v] of Object.entries(budgets)) params.set(ch, String(Math.round(v)));
  return `/api/forecast/export?${params.toString()}`;
}
