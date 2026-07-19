from pydantic import BaseModel


class CurvePoint(BaseModel):
    budget_multiplier: float
    spend: float
    revenue_p50: float
    roas_p50: float


class ChannelCurve(BaseModel):
    channel: str
    points: list[CurvePoint]


class SimulatorResponse(BaseModel):
    horizon_days: int
    curves: list[ChannelCurve]
