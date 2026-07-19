"""Budget response curves for the simulator tab."""

from backend.app.core.state import ModelStore
from backend.app.schemas.simulator import (ChannelCurve, CurvePoint,
                                           SimulatorResponse)
from backend.app.services.forecast_service import resolve_plan


def get_curves(store: ModelStore, horizon: int,
               budgets: dict[str, float] | None = None) -> SimulatorResponse:
    plan = resolve_plan(store, horizon, budgets)
    df = store.response_curves(horizon, plan)
    curves = []
    for ch, g in df.groupby("channel"):
        pts = [
            CurvePoint(
                budget_multiplier=round(float(r["budget_multiplier"]), 2),
                spend=round(float(r["spend"])),
                revenue_p50=round(float(r["revenue_p50"])),
                roas_p50=round(float(r["roas_p50"]), 2),
            )
            for _, r in g.sort_values("budget_multiplier").iterrows()
        ]
        curves.append(ChannelCurve(channel=ch, points=pts))
    return SimulatorResponse(horizon_days=horizon, curves=curves)
