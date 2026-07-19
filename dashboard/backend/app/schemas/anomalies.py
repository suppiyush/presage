from pydantic import BaseModel


class RegimeShift(BaseModel):
    channel: str
    historical_roas: float
    recent_roas: float
    change_pct: float
    severity: str


class WeeklyAnomaly(BaseModel):
    channel: str
    week_start: str
    actual_roas: float
    expected_roas: float
    deviation_sigma: float
    direction: str


class WeeklyRoasPoint(BaseModel):
    channel: str
    week_start: str
    roas: float


class AnomaliesResponse(BaseModel):
    regime_shifts: list[RegimeShift]
    weekly_anomalies: list[WeeklyAnomaly]
    weekly_roas: list[WeeklyRoasPoint]
