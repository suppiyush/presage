"""Optimizer results with per-channel rationale strings.

The rationale is derived from the data (regime shifts, direction and size of
the suggested change) so the UI never has to invent copy.
"""

from backend.app.core.state import ModelStore
from backend.app.schemas.allocation import AllocationResponse, ChannelAllocation
from backend.app.services.forecast_service import resolve_plan

_GUARDRAIL_PCT = 40.0
_AT_BOUND_TOLERANCE = 0.5  # percentage points


def _rationale(channel: str, change_pct: float, at_guardrail: bool,
               shift_by_channel: dict[str, dict]) -> str:
    shift = shift_by_channel.get(channel)
    if shift and shift["change_pct"] < 0:
        base = (f"ROAS has fallen {abs(shift['change_pct']):.0f}% "
                f"({shift['historical_roas']}x to {shift['recent_roas']}x)")
        if at_guardrail and change_pct < 0:
            return f"{base}; cut limited by the guardrail"
        return f"{base}; budget moved toward stronger channels"
    if change_pct > 1:
        return "Response curve shows remaining headroom at strong ROAS"
    if change_pct < -1:
        return "Efficiency has softened at the current spend level"
    return "Already close to its best observed spend level"


def get_allocation(store: ModelStore, horizon: int,
                   budgets: dict[str, float] | None = None) -> AllocationResponse:
    plan = resolve_plan(store, horizon, budgets)
    opt = store.optimizer(horizon, plan)
    shifts = store.regime_shifts()
    shift_by_channel = {r["channel"]: r for r in shifts.to_dict("records")}

    channels = []
    for ch in opt["channels"]:
        cur = float(opt["current_plan"][ch])
        new = float(opt["optimal_plan"][ch])
        change_pct = (new / cur - 1) * 100 if cur else 0.0
        at_guardrail = abs(abs(change_pct) - _GUARDRAIL_PCT) <= _AT_BOUND_TOLERANCE
        channels.append(ChannelAllocation(
            channel=ch,
            current=round(cur), suggested=round(new),
            change_pct=round(change_pct, 1),
            at_guardrail=at_guardrail,
            rationale=_rationale(ch, change_pct, at_guardrail, shift_by_channel),
        ))

    return AllocationResponse(
        horizon_days=horizon,
        current_revenue_p50=round(float(opt["current_revenue_p50"])),
        optimal_revenue_p50=round(float(opt["optimal_revenue_p50"])),
        lift_abs=round(float(opt["lift_abs"])),
        lift_pct=round(float(opt["lift_pct"]), 1),
        bounds_note=opt["bounds_note"],
        channels=channels,
    )
