"""Bootstrap payload: everything the UI needs before the first interaction."""

from backend.app.core.config import settings
from backend.app.core.state import ModelStore
from backend.app.schemas.meta import (Calibration, HorizonBand, MetaResponse,
                                      TrailingActuals)


def get_meta(store: ModelStore) -> MetaResponse:
    default_plans = {
        h: {ch: round(v, 2) for ch, v in store.default_plan(h).items()}
        for h in store.horizons
    }

    bands = []
    for h in store.horizons:
        g = store.forecast(h)
        p10 = float(g["revenue_p10"].sum())
        p50 = float(g["revenue_p50"].sum())
        p90 = float(g["revenue_p90"].sum())
        bands.append(HorizonBand(
            horizon_days=h,
            revenue_p10=round(p10), revenue_p50=round(p50), revenue_p90=round(p90),
            width_pct=round((p90 - p10) / 2 / p50 * 100, 1) if p50 else 0.0,
        ))

    trailing = store.trailing_actuals(settings.trailing_weeks)
    cal = store.calibration
    return MetaResponse(
        horizons=store.horizons,
        channels=store.channels,
        default_plans=default_plans,
        calibration=Calibration(
            inside=round(cal["inside"], 4),
            below_p10=round(cal["below_p10"], 4),
            above_p90=round(cal["above_p90"], 4),
        ),
        trailing=TrailingActuals(
            spend=round(trailing["spend"]),
            revenue=round(trailing["revenue"]),
            roas=round(trailing["roas"], 2),
        ),
        horizon_bands=bands,
        last_data_date=store.last_data_date,
    )
