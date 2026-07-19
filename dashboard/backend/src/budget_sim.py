"""Budget scenario simulation and optimal allocation.

- Response curves: sweep each channel's budget 50% -> 200% of plan and
  forecast revenue at each level (diminishing-returns curves).
- Optimizer: scipy SLSQP, maximize total P50 revenue subject to the budget
  constraint, with SYMMETRIC +/-40% bounds around the current plan.

Why symmetric bounds (learned the hard way):
  * Naive wide bounds let the optimizer push ~30x historical spend into a tiny
    channel — pure extrapolation, garbage lift claims.
  * Historical min/max bounds can force money OUT of a strong channel
    (asymmetric ceiling below current spend) producing negative lift.
Never let the optimizer leave the vicinity of historically observed spend.

No network access — safe to import anywhere, but not used by run.sh.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src import schema
from src.predict import derive_budget_plan, forecast_groups


def _total_p50(bundle, feats, horizon_days, budget_plan) -> float:
    groups = forecast_groups(bundle, feats, horizon_days, budget_plan)
    return float(groups["revenue_p50"].sum())


def response_curves(bundle, feats, horizon_days=30, budget_plan=None,
                    lo=0.5, hi=2.0, points=15) -> pd.DataFrame:
    """Per-channel revenue/ROAS response to budget scaling (others held at plan)."""
    if budget_plan is None:
        budget_plan = derive_budget_plan(feats, horizon_days)

    records = []
    for ch in budget_plan:
        for mult in np.linspace(lo, hi, points):
            plan = dict(budget_plan)
            plan[ch] = budget_plan[ch] * mult
            groups = forecast_groups(bundle, feats, horizon_days, plan)
            ch_rows = groups[groups["channel"] == ch]
            spend = float(ch_rows["spend"].sum())
            rev = float(ch_rows["revenue_p50"].sum())
            records.append({
                "channel": ch,
                "budget_multiplier": round(float(mult), 3),
                "spend": spend,
                "revenue_p50": rev,
                "roas_p50": rev / spend if spend > 0 else 0.0,
            })
    return pd.DataFrame(records)


def optimize_allocation(bundle, feats, horizon_days=30, budget_plan=None) -> dict:
    """Reallocate the total budget across channels to maximize P50 revenue.

    Bounds: [60%, 140%] of each channel's current plan — inside the
    historically observed spend range, where the model interpolates rather
    than extrapolates.
    """
    if budget_plan is None:
        budget_plan = derive_budget_plan(feats, horizon_days)
    channels = sorted(budget_plan)
    x0 = np.array([budget_plan[c] for c in channels])
    total = float(x0.sum())

    def objective(x):
        plan = dict(zip(channels, x))
        return -_total_p50(bundle, feats, horizon_days, plan)

    bounds = [(budget_plan[c] * schema.OPTIMIZER_BOUND_LOW,
               budget_plan[c] * schema.OPTIMIZER_BOUND_HIGH) for c in channels]
    constraints = [{"type": "eq", "fun": lambda x: x.sum() - total}]

    result = minimize(objective, x0, method="SLSQP", bounds=bounds,
                      constraints=constraints,
                      options={"maxiter": 60, "ftol": 1e-2})

    current_rev = _total_p50(bundle, feats, horizon_days, budget_plan)
    optimal_plan = dict(zip(channels, [float(v) for v in result.x]))
    optimal_rev = _total_p50(bundle, feats, horizon_days, optimal_plan)

    # If the optimizer failed to improve, the honest answer is "hold the plan".
    if optimal_rev < current_rev:
        optimal_plan, optimal_rev = dict(budget_plan), current_rev

    return {
        "horizon_days": horizon_days,
        "channels": channels,
        "current_plan": {c: float(budget_plan[c]) for c in channels},
        "optimal_plan": optimal_plan,
        "current_revenue_p50": current_rev,
        "optimal_revenue_p50": optimal_rev,
        "lift_abs": optimal_rev - current_rev,
        "lift_pct": (optimal_rev / current_rev - 1.0) * 100 if current_rev else 0.0,
        "bounds_note": (f"channel budgets constrained to "
                        f"[{schema.OPTIMIZER_BOUND_LOW:.0%}, "
                        f"{schema.OPTIMIZER_BOUND_HIGH:.0%}] of current plan to "
                        f"avoid extrapolating beyond observed spend"),
    }
