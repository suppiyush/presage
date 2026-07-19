from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    horizon: int = Field(30, description="Forecast horizon in days")
    budgets: dict[str, float] | None = Field(
        None, description="Per-channel period budgets; omitted channels use defaults")


class GroupForecast(BaseModel):
    channel: str
    campaign_type: str
    spend: float
    revenue_p10: float
    revenue_p50: float
    revenue_p90: float
    roas_p50: float


class ChannelForecast(BaseModel):
    channel: str
    spend: float
    revenue_p10: float
    revenue_p50: float
    revenue_p90: float
    roas_p50: float


class ForecastTotals(BaseModel):
    spend: float
    revenue_p10: float
    revenue_p50: float
    revenue_p90: float
    roas_p50: float
    vs_recent_pace_pct: float  # P50 revenue vs trailing actuals scaled to horizon
    trailing_roas: float
    roas_vs_trailing_pct: float


class ForecastResponse(BaseModel):
    horizon_days: int
    totals: ForecastTotals
    by_channel: list[ChannelForecast]
    groups: list[GroupForecast]
