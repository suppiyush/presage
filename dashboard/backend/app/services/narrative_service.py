"""Plain-language summary generation.

Builds the model context and delegates to src.ai_narrative (Gemini ->
Hugging Face -> template). This is the only service that can make a network
call; it must stay off the scoring path.
"""

from datetime import datetime, timezone

from backend.app.core.config import settings
from backend.app.core.state import ModelStore
from backend.app.schemas.narrative import NarrativeResponse
from backend.app.services.forecast_service import resolve_plan
from src.ai_narrative import build_context, generate_narrative

_TOP_TYPES = 3
_RECENT_ANOMALIES = 10


def make_narrative(store: ModelStore, horizon: int,
                   budgets: dict[str, float] | None) -> NarrativeResponse:
    plan = resolve_plan(store, horizon, budgets)
    groups = store.forecast(horizon, plan)

    spend = float(groups["spend"].sum())
    rev = {q: float(groups[f"revenue_{q}"].sum()) for q in ("p10", "p50", "p90")}

    ch_ctx = []
    for ch, g in groups.groupby("channel"):
        top = g.nlargest(_TOP_TYPES, "revenue_p50")
        ch_spend = float(g["spend"].sum())
        ch_rev = float(g["revenue_p50"].sum())
        ch_ctx.append({
            "channel": ch,
            "spend": round(ch_spend),
            "revenue": round(ch_rev),
            "roas": round(ch_rev / ch_spend, 2) if ch_spend else 0.0,
            "top_campaign_types": [
                {"type": r["campaign_type"], "roas_p50": round(float(r["roas_p50"]), 2)}
                for _, r in top.iterrows()],
        })

    trailing = store.trailing_actuals(settings.trailing_weeks)
    opt = store.optimizer(horizon, plan)
    cal = store.calibration

    ctx = build_context(
        forecast_total={"horizon_days": horizon, "spend": round(spend),
                        "revenue_p10": round(rev["p10"]),
                        "revenue_p50": round(rev["p50"]),
                        "revenue_p90": round(rev["p90"]),
                        "roas_p50": round(rev["p50"] / spend, 2) if spend else 0.0},
        trailing={"spend": round(trailing["spend"]),
                  "revenue": round(trailing["revenue"]),
                  "roas": round(trailing["roas"], 2)},
        channels=ch_ctx,
        anomalies=store.weekly_anomalies().tail(_RECENT_ANOMALIES).to_dict("records"),
        regime_shifts=store.regime_shifts().to_dict("records"),
        optimizer={"lift_pct": round(float(opt["lift_pct"]), 1),
                   "action": "hold the current mix; re-diagnose any channel "
                             "with a flagged ROAS regime shift",
                   "note": opt["bounds_note"]},
        calibration={"coverage_pct": f"{cal['inside']:.1%}", "nominal": "80%",
                     "method": "conformalized quantile regression"},
        seasonality_note="Yearly and Black-Friday/Cyber-Monday seasonality "
                         "encoded via Fourier terms and holiday flags.",
    )
    text, provider = generate_narrative(ctx)
    return NarrativeResponse(
        text=text, provider=provider,
        generated_at=datetime.now(timezone.utc).strftime("%b %d, %Y · %H:%M UTC"),
    )
