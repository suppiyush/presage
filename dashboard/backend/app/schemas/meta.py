from pydantic import BaseModel


class Calibration(BaseModel):
    inside: float
    below_p10: float
    above_p90: float


class TrailingActuals(BaseModel):
    spend: float
    revenue: float
    roas: float


class HorizonBand(BaseModel):
    horizon_days: int
    revenue_p10: float
    revenue_p50: float
    revenue_p90: float
    width_pct: float  # half-width of the P10-P90 band as % of P50


class MetaResponse(BaseModel):
    horizons: list[int]
    channels: list[str]
    default_plans: dict[int, dict[str, float]]
    calibration: Calibration
    trailing: TrailingActuals
    horizon_bands: list[HorizonBand]
    last_data_date: str
