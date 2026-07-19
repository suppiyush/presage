from pydantic import BaseModel


class ChannelAllocation(BaseModel):
    channel: str
    current: float
    suggested: float
    change_pct: float
    at_guardrail: bool
    rationale: str


class AllocationResponse(BaseModel):
    horizon_days: int
    current_revenue_p50: float
    optimal_revenue_p50: float
    lift_abs: float
    lift_pct: float
    bounds_note: str
    channels: list[ChannelAllocation]
