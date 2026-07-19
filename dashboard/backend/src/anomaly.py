"""ROAS anomaly detection.

Scans weekly blended ROAS per channel and flags weeks deviating more than
1.5 standard deviations from the rolling mean. Also reports regime shifts
(recent ROAS vs long-run average) — this is what surfaces a silent channel
efficiency collapse automatically.

No network access.
"""

import numpy as np
import pandas as pd

Z_THRESHOLD = 1.5
ROLL_WINDOW = 8
RECENT_WEEKS = 4


def detect_anomalies(feats: pd.DataFrame) -> pd.DataFrame:
    """Weekly ROAS anomalies per channel.

    Returns records: channel, week_start, actual_roas, expected_roas,
    deviation_sigma, direction.
    """
    wk = (feats.groupby(["channel", "week_start"], as_index=False)
               [["spend", "revenue"]].sum())
    wk["roas"] = wk["revenue"] / wk["spend"]
    wk = wk.sort_values(["channel", "week_start"])

    records = []
    for ch, g in wk.groupby("channel"):
        roll_mean = g["roas"].shift(1).rolling(ROLL_WINDOW, min_periods=4).mean()
        roll_std = g["roas"].shift(1).rolling(ROLL_WINDOW, min_periods=4).std()
        z = (g["roas"] - roll_mean) / roll_std.replace(0, np.nan)
        flagged = g[z.abs() > Z_THRESHOLD]
        for idx, row in flagged.iterrows():
            records.append({
                "channel": ch,
                "week_start": row["week_start"],
                "actual_roas": round(float(row["roas"]), 2),
                "expected_roas": round(float(roll_mean.loc[idx]), 2),
                "deviation_sigma": round(float(z.loc[idx]), 2),
                "direction": "above" if z.loc[idx] > 0 else "below",
            })
    return pd.DataFrame(records,
                        columns=["channel", "week_start", "actual_roas",
                                 "expected_roas", "deviation_sigma", "direction"])


def detect_regime_shifts(feats: pd.DataFrame, threshold=0.35) -> pd.DataFrame:
    """Channels whose recent ROAS diverges >threshold (35%) from their
    long-run average — e.g. a silent efficiency collapse.
    """
    wk = (feats.groupby(["channel", "week_start"], as_index=False)
               [["spend", "revenue"]].sum())
    wk["roas"] = wk["revenue"] / wk["spend"]

    records = []
    for ch, g in wk.groupby("channel"):
        g = g.sort_values("week_start")
        hist, recent = g.iloc[:-RECENT_WEEKS], g.tail(RECENT_WEEKS)
        if len(hist) < ROLL_WINDOW or recent["spend"].sum() <= 0:
            continue
        hist_roas = hist["revenue"].sum() / hist["spend"].sum()
        recent_roas = recent["revenue"].sum() / recent["spend"].sum()
        change = recent_roas / hist_roas - 1.0 if hist_roas else 0.0
        if abs(change) >= threshold:
            records.append({
                "channel": ch,
                "historical_roas": round(float(hist_roas), 2),
                "recent_roas": round(float(recent_roas), 2),
                "change_pct": round(float(change * 100), 1),
                "severity": "high" if abs(change) >= 0.5 else "medium",
            })
    return pd.DataFrame(records,
                        columns=["channel", "historical_roas", "recent_roas",
                                 "change_pct", "severity"])
