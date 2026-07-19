"""Forecast generation: features + model bundle -> predictions.csv.

CLI:
    python -m src.predict --features ./output/features.parquet \
                          --model ./pickle/model.pkl \
                          --output ./output/predictions.csv

Scoring path: NO network access, no interactivity. Horizons are relative to
the last date present in the data — never a hardcoded calendar date.

The forecast machinery (forecast_groups / derive_budget_plan) is also reused
by src/budget_sim.py for scenario simulation and optimization.
"""

import argparse
import os
import pickle

import numpy as np
import pandas as pd

from src import schema
from src.generate_features import calendar_features, encode
from src.train import enforce_monotonic


def load_bundle(model_path: str) -> dict:
    with open(model_path, "rb") as f:
        return pickle.load(f)


def weeks_ahead(horizon_days: int) -> int:
    return max(1, round(horizon_days / 7))


def _group_history(feats: pd.DataFrame) -> dict:
    """Per (channel, campaign_type): a trajectory buffer of the last observed
    weeks as (revenue, spend, roas) tuples plus the last week_start. During
    recursive forecasting the buffer is extended with the model's own P50
    outcome for each predicted week, so lag/rolling features evolve instead
    of staying frozen at the last observed values.
    """
    history = {}
    for (ch, ct), g in feats.groupby(["channel", "campaign_type"]):
        g = g.sort_values("week_start")
        tail = g.tail(max(schema.ROLL_WEEKS, 4))
        history[(ch, ct)] = {
            "traj": [(float(r), float(s), float(x)) for r, s, x in
                     zip(tail["revenue"], tail["spend"], tail["roas"])],
            "last_week_start": g["week_start"].max(),
        }
    return history


def _features_from_traj(traj: list) -> dict:
    """Lag/rolling features from a trajectory buffer (observed + predicted)."""
    tail = traj[-schema.ROLL_WEEKS:]
    return {
        "revenue_lag_1w": traj[-1][0],
        "revenue_lag_4w": traj[-4][0] if len(traj) >= 4 else traj[0][0],
        "spend_lag_1w": traj[-1][1],
        "roas_lag_1w": traj[-1][2],
        "revenue_roll_4w": float(np.mean([t[0] for t in tail])),
        "spend_roll_4w": float(np.mean([t[1] for t in tail])),
        "roas_roll_4w": float(np.mean([t[2] for t in tail])),
    }


def _channel_shares(bundle: dict, feats: pd.DataFrame) -> pd.DataFrame:
    """Spend share per campaign_type within channel, restricted to groups
    present in THIS data and renormalized.

    Prefers the bundle's persisted shares (computed on full training history);
    falls back to shares observed in the current data for channels/groups the
    bundle has never seen.
    """
    present = (feats.groupby(["channel", "campaign_type"], as_index=False)["spend"]
                    .sum().rename(columns={"spend": "observed_spend"}))
    share = present.merge(bundle["spend_share"], on=["channel", "campaign_type"],
                          how="left")

    # Groups unknown to the bundle: use their observed share within channel.
    obs_totals = present.groupby("channel")["observed_spend"].transform("sum")
    observed_share = present["observed_spend"] / obs_totals
    share["share"] = share["share"].fillna(observed_share)

    # Renormalize within channel over the groups actually present.
    totals = share.groupby("channel")["share"].transform("sum")
    share["share"] = np.where(totals > 0, share["share"] / totals, 0.0)
    return share[["channel", "campaign_type", "share"]]


def derive_budget_plan(feats: pd.DataFrame, horizon_days: int) -> dict:
    """Default budget: continue current pacing. Channel weekly spend averaged
    over the trailing 4 observed weeks, times the number of forecast weeks.
    """
    n_weeks = weeks_ahead(horizon_days)
    plan = {}
    for ch, g in feats.groupby("channel"):
        wk = g.groupby("week_start")["spend"].sum().sort_index()
        plan[ch] = float(wk.tail(schema.ROLL_WEEKS).mean()) * n_weeks
    return plan


def forecast_groups(bundle: dict, feats: pd.DataFrame, horizon_days: int,
                    budget_plan: dict | None = None,
                    return_weekly: bool = False) -> pd.DataFrame:
    """Forecast per (channel, campaign_type) over the horizon.

    Recursive multi-step strategy: weeks are predicted one at a time (batched
    across groups); after each week the model's P50 outcome is appended to the
    group's trajectory so the next week's lag/rolling features evolve with the
    forecast. P10/P90 are predicted conditional on that median path each week
    (recursing each quantile on its own path would compound quantiles and
    inflate the band).

    Period bands aggregate weekly bands with the empirically estimated
    week-to-week residual correlation rho (bundle["weekly_error_corr"]):

        half = sqrt( rho * (sum d_i)^2 + (1 - rho) * sum d_i^2 )

    rho=1 reduces to the old plain sum (perfect correlation), rho=0 is the
    independence bound. Old bundles without the field behave as before.

    Returns one row per group with total spend, revenue_p10/50/90 and period
    roas_p10/50/90 — or the raw weekly rows when return_weekly=True.
    """
    n_weeks = weeks_ahead(horizon_days)
    if budget_plan is None:
        budget_plan = derive_budget_plan(feats, horizon_days)

    history = _group_history(feats)
    shares = _channel_shares(bundle, feats)

    # Active groups with their constant weekly spend under the plan.
    active = []
    for _, s in shares.iterrows():
        ch, ct, share = s["channel"], s["campaign_type"], float(s["share"])
        if share <= 0 or (ch, ct) not in history or ch not in budget_plan:
            continue  # skip types with zero share — see docs/methodology.md
        week_spend = budget_plan[ch] * share / n_weeks
        if week_spend > 0:
            active.append((ch, ct, week_spend))
    if not active:
        raise ValueError("No forecastable groups — check data volume and spend shares")

    key_df = pd.DataFrame([(ch, ct) for ch, ct, _ in active],
                          columns=["channel", "campaign_type"])
    channel_codes = encode(key_df["channel"], bundle["channel_enc"]).values
    camptype_codes = encode(key_df["campaign_type"], bundle["camptype_enc"]).values
    corr = bundle["conformal_correction"]

    weekly_frames = []
    for w in range(1, n_weeks + 1):
        rows = []
        for ch, ct, week_spend in active:
            h = history[(ch, ct)]
            ws = h["last_week_start"] + pd.Timedelta(weeks=w)
            rows.append({"spend": week_spend,
                         **_features_from_traj(h["traj"]),
                         **calendar_features(ws)})
        X = pd.DataFrame(rows)
        X["channel_code"] = channel_codes
        X["camptype_code"] = camptype_codes
        X = X[bundle["feature_cols"]]

        p10 = bundle["p10"].predict(X) - corr
        p50 = bundle["p50"].predict(X)
        p90 = bundle["p90"].predict(X) + corr
        p10, p50, p90 = enforce_monotonic(p10, p50, p90)

        wk = key_df.copy()
        wk["week"] = w
        wk["spend"] = X["spend"].values
        wk["revenue_p10"] = wk["spend"] * p10
        wk["revenue_p50"] = wk["spend"] * p50
        wk["revenue_p90"] = wk["spend"] * p90
        weekly_frames.append(wk)

        # Recursive update: feed the median outcome back into each trajectory.
        for i, (ch, ct, week_spend) in enumerate(active):
            history[(ch, ct)]["traj"].append(
                (week_spend * float(p50[i]), week_spend, float(p50[i])))

    weekly = pd.concat(weekly_frames, ignore_index=True)
    if return_weekly:
        return weekly

    # Correlation-adjusted aggregation of weekly bands into the period band.
    rho = float(bundle.get("weekly_error_corr", 1.0))
    weekly["d_low"] = (weekly["revenue_p50"] - weekly["revenue_p10"]).clip(lower=0)
    weekly["d_high"] = (weekly["revenue_p90"] - weekly["revenue_p50"]).clip(lower=0)
    weekly["d_low_sq"] = weekly["d_low"] ** 2
    weekly["d_high_sq"] = weekly["d_high"] ** 2
    agg = weekly.groupby(["channel", "campaign_type"], as_index=False).agg(
        spend=("spend", "sum"),
        revenue_p50=("revenue_p50", "sum"),
        d_low=("d_low", "sum"),
        d_high=("d_high", "sum"),
        d_low_sq=("d_low_sq", "sum"),
        d_high_sq=("d_high_sq", "sum"),
    )
    half_low = np.sqrt(rho * agg["d_low"] ** 2 + (1 - rho) * agg["d_low_sq"])
    half_high = np.sqrt(rho * agg["d_high"] ** 2 + (1 - rho) * agg["d_high_sq"])
    agg["revenue_p10"] = (agg["revenue_p50"] - half_low).clip(lower=0)
    agg["revenue_p90"] = agg["revenue_p50"] + half_high

    out = agg[["channel", "campaign_type", "spend",
               "revenue_p10", "revenue_p50", "revenue_p90"]].copy()
    for q in ("p10", "p50", "p90"):
        out[f"roas_{q}"] = out[f"revenue_{q}"] / out["spend"]
    out["horizon_days"] = horizon_days
    return out


def _rollup(groups: pd.DataFrame, by: list) -> pd.DataFrame:
    agg = groups.groupby(by, as_index=False)[
        ["spend", "revenue_p10", "revenue_p50", "revenue_p90"]].sum()
    for q in ("p10", "p50", "p90"):
        agg[f"roas_{q}"] = agg[f"revenue_{q}"] / agg["spend"]
    return agg


def build_predictions(bundle: dict, feats: pd.DataFrame) -> pd.DataFrame:
    """All horizons x all granularities, in the OUTPUT_COLUMNS schema."""
    frames = []
    for horizon in schema.HORIZONS_DAYS:
        groups = forecast_groups(bundle, feats, horizon)

        total = _rollup(groups, ["horizon_days"])
        total["channel"] = schema.AGGREGATE_LABEL
        total["campaign_type"] = schema.AGGREGATE_LABEL

        channels = _rollup(groups, ["horizon_days", "channel"])
        channels["campaign_type"] = schema.AGGREGATE_LABEL

        frames += [total, channels, groups]
        print(f"[predict] {horizon}d: revenue P10 ${total['revenue_p10'].iloc[0]:,.0f} | "
              f"P50 ${total['revenue_p50'].iloc[0]:,.0f} | "
              f"P90 ${total['revenue_p90'].iloc[0]:,.0f} | "
              f"blended ROAS P50 {total['roas_p50'].iloc[0]:.2f}x")

    preds = pd.concat(frames, ignore_index=True)
    preds = preds[schema.OUTPUT_COLUMNS]
    for col in schema.OUTPUT_COLUMNS[3:]:
        preds[col] = preds[col].round(4)
    return preds


def main():
    ap = argparse.ArgumentParser(description="Generate predictions.csv")
    ap.add_argument("--features", default="./output/features.parquet")
    ap.add_argument("--model", default="./pickle/model.pkl")
    ap.add_argument("--output", default="./output/predictions.csv")
    args = ap.parse_args()

    bundle = load_bundle(args.model)
    feats = pd.read_parquet(args.features)

    preds = build_predictions(bundle, feats)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    preds.to_csv(args.output, index=False)  # fresh write, never append
    print(f"[predict] wrote {len(preds)} rows -> {args.output}")


if __name__ == "__main__":
    main()
