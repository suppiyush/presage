"""Feature generation: cleaned daily data -> weekly feature table (parquet).

CLI:
    python -m src.generate_features --data-dir ./data --out ./output/features.parquet

Also exposes the calendar/seasonality helpers reused by predict.py to build
feature rows for future weeks. NO network access — scoring path.
"""

import argparse
import os

import holidays as holidays_lib
import numpy as np
import pandas as pd

from src import ingest, schema, validate

_US_HOLIDAYS = holidays_lib.US(years=range(2020, 2035))


def calendar_features(week_start: pd.Timestamp) -> dict:
    """Calendar / seasonality features for the week beginning `week_start`."""
    week_start = pd.Timestamp(week_start)
    woy = int(week_start.isocalendar().week)
    days = [week_start + pd.Timedelta(days=i) for i in range(7)]
    return {
        "month": int(week_start.month),
        "quarter": int(week_start.quarter),
        "week_of_year": woy,
        "is_holiday_week": int(any(d.date() in _US_HOLIDAYS for d in days)),
        "is_bfcm": int(week_start.month == 11 and 47 <= woy <= 48),
        "sin_52": float(np.sin(2 * np.pi * woy / 52)),
        "cos_52": float(np.cos(2 * np.pi * woy / 52)),
        "sin_26": float(np.sin(2 * np.pi * woy / 26)),
        "cos_26": float(np.cos(2 * np.pi * woy / 26)),
    }


def build_encoders(df: pd.DataFrame) -> tuple[dict, dict]:
    """Deterministic label encoders (plain dicts — robust to unpickling)."""
    channel_enc = {c: i for i, c in enumerate(sorted(df["channel"].unique()))}
    camptype_enc = {c: i for i, c in enumerate(sorted(df["campaign_type"].unique()))}
    return channel_enc, camptype_enc


def encode(series: pd.Series, enc: dict) -> pd.Series:
    """Encode labels; unseen labels get code -1 (XGBoost handles it numerically)."""
    return series.map(enc).fillna(-1).astype(int)


def weekly_table(daily: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily -> weekly per (channel, campaign_type)."""
    df = daily.copy()
    df["week_start"] = df["date"].dt.to_period("W").dt.start_time
    wk = (df.groupby(["channel", "campaign_type", "week_start"], as_index=False)
            [["spend", "revenue"]].sum())
    wk = wk[wk["spend"] > 0].copy()
    wk["roas"] = wk["revenue"] / wk["spend"]

    # Drop sparse groups: too little history to learn from.
    counts = wk.groupby(["channel", "campaign_type"])["week_start"].transform("count")
    dropped = wk[counts < schema.MIN_WEEKS]
    if len(dropped):
        names = dropped.groupby(["channel", "campaign_type"]).size()
        for (ch, ct), n in names.items():
            print(f"[features] dropped sparse group {ch}/{ct} ({n} weeks "
                  f"< {schema.MIN_WEEKS})")
    wk = wk[counts >= schema.MIN_WEEKS].copy()
    return wk.sort_values(["channel", "campaign_type", "week_start"]).reset_index(drop=True)


def add_features(wk: pd.DataFrame, channel_enc: dict, camptype_enc: dict) -> pd.DataFrame:
    """Add lag/rolling/calendar features. Lags shift(1) BEFORE rolling — no leakage."""
    df = wk.sort_values(["channel", "campaign_type", "week_start"]).copy()
    grp = df.groupby(["channel", "campaign_type"])

    df["revenue_lag_1w"] = grp["revenue"].shift(1)
    df["revenue_lag_4w"] = grp["revenue"].shift(4)
    df["spend_lag_1w"] = grp["spend"].shift(1)
    df["roas_lag_1w"] = grp["roas"].shift(1)
    for col in ("revenue", "spend", "roas"):
        df[f"{col}_roll_4w"] = grp[col].transform(
            lambda s: s.shift(1).rolling(schema.ROLL_WEEKS, min_periods=2).mean()
        )

    cal = pd.DataFrame([calendar_features(ws) for ws in df["week_start"]],
                       index=df.index)
    df = pd.concat([df, cal], axis=1)

    df["channel_code"] = encode(df["channel"], channel_enc)
    df["camptype_code"] = encode(df["campaign_type"], camptype_enc)

    before = len(df)
    df = df.dropna(subset=["revenue_lag_1w", "roas_lag_1w", "revenue_roll_4w"])
    print(f"[features] dropped {before - len(df)} rows with NaN lags")
    # revenue_lag_4w may still be NaN early in a group's life; backfill with the
    # 1-week lag so the row remains usable.
    df["revenue_lag_4w"] = df["revenue_lag_4w"].fillna(df["revenue_lag_1w"])
    return df.reset_index(drop=True)


def spend_share(weekly: pd.DataFrame) -> pd.DataFrame:
    """Historical spend share of each campaign_type within its channel.

    Uses merge, not groupby().apply() — the latter raises
    "ValueError: cannot insert channel, already exists".
    """
    type_spend = (weekly.groupby(["channel", "campaign_type"], as_index=False)
                        ["spend"].sum())
    channel_totals = (weekly.groupby("channel", as_index=False)["spend"].sum()
                            .rename(columns={"spend": "channel_total"}))
    share = type_spend.merge(channel_totals, on="channel")
    share["share"] = share["spend"] / share["channel_total"]
    return share[["channel", "campaign_type", "share"]]


def generate(data_dir: str) -> pd.DataFrame:
    """Full pipeline: ingest -> validate -> clean -> weekly features."""
    raw = ingest.load_raw(data_dir)
    report = validate.validate(raw)
    report.raise_if_failed()          # abort on hard errors, proceed on warnings

    daily = ingest.clean(raw)
    wk = weekly_table(daily)
    channel_enc, camptype_enc = build_encoders(wk)
    feats = add_features(wk, channel_enc, camptype_enc)

    # Anchor for forecast horizons: the last date actually present in the data.
    feats["data_end_date"] = daily["date"].max()

    n_groups = feats.groupby(["channel", "campaign_type"]).ngroups
    print(f"[features] final table: {len(feats):,} rows x {feats.shape[1]} cols, "
          f"{n_groups} groups, "
          f"{feats['week_start'].min():%Y-%m-%d} -> {feats['week_start'].max():%Y-%m-%d}")
    return feats


def main():
    ap = argparse.ArgumentParser(description="Generate the weekly feature table")
    ap.add_argument("--data-dir", default="./data")
    ap.add_argument("--out", default="./output/features.parquet")
    args = ap.parse_args()

    feats = generate(args.data_dir)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    feats.to_parquet(args.out, index=False)
    print(f"[features] wrote {args.out}")


if __name__ == "__main__":
    main()
