"""Regime shifts, weekly anomalies and the weekly ROAS series."""

from backend.app.core.state import ModelStore
from backend.app.schemas.anomalies import (AnomaliesResponse, RegimeShift,
                                           WeeklyAnomaly, WeeklyRoasPoint)

_RECENT_ANOMALIES = 25


def get_anomalies(store: ModelStore) -> AnomaliesResponse:
    shifts = [
        RegimeShift(
            channel=r["channel"],
            historical_roas=float(r["historical_roas"]),
            recent_roas=float(r["recent_roas"]),
            change_pct=round(float(r["change_pct"]), 1),
            severity=str(r["severity"]),
        )
        for r in store.regime_shifts().to_dict("records")
    ]

    weekly = [
        WeeklyAnomaly(
            channel=r["channel"],
            week_start=str(r["week_start"])[:10],
            actual_roas=round(float(r["actual_roas"]), 2),
            expected_roas=round(float(r["expected_roas"]), 2),
            deviation_sigma=round(float(r["deviation_sigma"]), 1),
            direction=str(r["direction"]),
        )
        for r in store.weekly_anomalies().tail(_RECENT_ANOMALIES).to_dict("records")
    ]

    series = [
        WeeklyRoasPoint(
            channel=r["channel"],
            week_start=str(r["week_start"])[:10],
            roas=round(float(r["roas"]), 2),
        )
        for r in store.weekly_channel_roas().to_dict("records")
    ]

    return AnomaliesResponse(regime_shifts=shifts, weekly_anomalies=weekly,
                             weekly_roas=series)
