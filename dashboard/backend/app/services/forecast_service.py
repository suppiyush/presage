"""Forecast queries: totals, per-channel and per-campaign-type breakdowns."""

import pandas as pd

from backend.app.core.config import settings
from backend.app.core.state import ModelStore
from backend.app.schemas.forecast import (ChannelForecast, ForecastResponse,
                                          ForecastTotals, GroupForecast)

_TRAILING_DAYS_PER_WEEK = 7


def resolve_plan(store: ModelStore, horizon: int,
                 budgets: dict[str, float] | None) -> dict[str, float]:
    """Merge user budget overrides onto the default pacing-based plan."""
    plan = dict(store.default_plan(horizon))
    for ch, value in (budgets or {}).items():
        if ch in plan and value is not None and value > 0:
            plan[ch] = float(value)
    return plan


def get_forecast(store: ModelStore, horizon: int,
                 budgets: dict[str, float] | None) -> ForecastResponse:
    plan = resolve_plan(store, horizon, budgets)
    groups = store.forecast(horizon, plan)

    spend = float(groups["spend"].sum())
    p10 = float(groups["revenue_p10"].sum())
    p50 = float(groups["revenue_p50"].sum())
    p90 = float(groups["revenue_p90"].sum())

    trailing = store.trailing_actuals(settings.trailing_weeks)
    trailing_days = settings.trailing_weeks * _TRAILING_DAYS_PER_WEEK
    # Scale trailing actual revenue to the forecast horizon for a fair pace check.
    paced_revenue = trailing["revenue"] * horizon / trailing_days
    roas_p50 = p50 / spend if spend else 0.0

    totals = ForecastTotals(
        spend=round(spend),
        revenue_p10=round(p10), revenue_p50=round(p50), revenue_p90=round(p90),
        roas_p50=round(roas_p50, 2),
        vs_recent_pace_pct=round((p50 / paced_revenue - 1) * 100, 1) if paced_revenue else 0.0,
        trailing_roas=round(trailing["roas"], 2),
        roas_vs_trailing_pct=round((roas_p50 / trailing["roas"] - 1) * 100, 1)
        if trailing["roas"] else 0.0,
    )

    by_channel = [
        ChannelForecast(
            channel=row["channel"],
            spend=round(row["spend"]),
            revenue_p10=round(row["revenue_p10"]),
            revenue_p50=round(row["revenue_p50"]),
            revenue_p90=round(row["revenue_p90"]),
            roas_p50=round(row["revenue_p50"] / row["spend"], 2) if row["spend"] else 0.0,
        )
        for _, row in groups.groupby("channel", as_index=False)[
            ["spend", "revenue_p10", "revenue_p50", "revenue_p90"]].sum().iterrows()
    ]

    group_rows = [
        GroupForecast(
            channel=r["channel"], campaign_type=r["campaign_type"],
            spend=round(r["spend"]),
            revenue_p10=round(r["revenue_p10"]),
            revenue_p50=round(r["revenue_p50"]),
            revenue_p90=round(r["revenue_p90"]),
            roas_p50=round(float(r["roas_p50"]), 2),
        )
        for _, r in groups.sort_values("revenue_p50", ascending=False).iterrows()
    ]

    return ForecastResponse(horizon_days=horizon, totals=totals,
                            by_channel=by_channel, groups=group_rows)


def forecast_csv(store: ModelStore, horizon: int,
                 budgets: dict[str, float] | None) -> str:
    plan = resolve_plan(store, horizon, budgets)
    groups = store.forecast(horizon, plan)
    cols = ["channel", "campaign_type", "spend",
            "revenue_p10", "revenue_p50", "revenue_p90",
            "roas_p10", "roas_p50", "roas_p90"]
    out: pd.DataFrame = groups[cols].copy()
    for c in cols[2:]:
        out[c] = out[c].round(4)
    return out.to_csv(index=False)
