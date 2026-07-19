export type Channel = string;

export interface Calibration {
  inside: number;
  below_p10: number;
  above_p90: number;
}

export interface TrailingActuals {
  spend: number;
  revenue: number;
  roas: number;
}

export interface HorizonBand {
  horizon_days: number;
  revenue_p10: number;
  revenue_p50: number;
  revenue_p90: number;
  width_pct: number;
}

export interface Meta {
  horizons: number[];
  channels: Channel[];
  default_plans: Record<string, Record<Channel, number>>;
  calibration: Calibration;
  trailing: TrailingActuals;
  horizon_bands: HorizonBand[];
  last_data_date: string;
}

export interface ForecastTotals {
  spend: number;
  revenue_p10: number;
  revenue_p50: number;
  revenue_p90: number;
  roas_p50: number;
  vs_recent_pace_pct: number;
  trailing_roas: number;
  roas_vs_trailing_pct: number;
}

export interface ChannelForecast {
  channel: Channel;
  spend: number;
  revenue_p10: number;
  revenue_p50: number;
  revenue_p90: number;
  roas_p50: number;
}

export interface GroupForecast extends ChannelForecast {
  campaign_type: string;
}

export interface Forecast {
  horizon_days: number;
  totals: ForecastTotals;
  by_channel: ChannelForecast[];
  groups: GroupForecast[];
}

export interface CurvePoint {
  budget_multiplier: number;
  spend: number;
  revenue_p50: number;
  roas_p50: number;
}

export interface ChannelCurve {
  channel: Channel;
  points: CurvePoint[];
}

export interface Simulator {
  horizon_days: number;
  curves: ChannelCurve[];
}

export interface ChannelAllocation {
  channel: Channel;
  current: number;
  suggested: number;
  change_pct: number;
  at_guardrail: boolean;
  rationale: string;
}

export interface Allocation {
  horizon_days: number;
  current_revenue_p50: number;
  optimal_revenue_p50: number;
  lift_abs: number;
  lift_pct: number;
  bounds_note: string;
  channels: ChannelAllocation[];
}

export interface RegimeShift {
  channel: Channel;
  historical_roas: number;
  recent_roas: number;
  change_pct: number;
  severity: string;
}

export interface WeeklyAnomaly {
  channel: Channel;
  week_start: string;
  actual_roas: number;
  expected_roas: number;
  deviation_sigma: number;
  direction: string;
}

export interface WeeklyRoasPoint {
  channel: Channel;
  week_start: string;
  roas: number;
}

export interface Anomalies {
  regime_shifts: RegimeShift[];
  weekly_anomalies: WeeklyAnomaly[];
  weekly_roas: WeeklyRoasPoint[];
}

export interface Narrative {
  text: string;
  provider: string;
  generated_at: string;
}

export type Budgets = Record<Channel, number>;
