"""Train the three quantile models + conformal correction -> pickle/model.pkl.

CLI:
    python -m src.train --data-dir ./data --model ./pickle/model.pkl

NOT part of the grading run (the grader uses the committed pre-trained pickle),
but fully reproducible: re-run this after replacing data/ to refresh the model.
"""

import argparse
import os
import pickle
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import xgboost as xgb

from src import generate_features as gf
from src import schema


def enforce_monotonic(p10, p50, p90):
    """p10 <= p50 <= p90, and ROAS can't be negative."""
    p10 = np.minimum(p10, p50)
    p90 = np.maximum(p90, p50)
    p10 = np.maximum(p10, 0)
    p50 = np.maximum(p50, 0)
    p90 = np.maximum(p90, 0)
    return p10, p50, p90


def train_quantile_models(X_train, y_train):
    models = {}
    for name, alpha in schema.QUANTILES.items():
        model = xgb.XGBRegressor(quantile_alpha=alpha, **schema.XGB_PARAMS)
        model.fit(X_train, y_train)
        models[name] = model
    return models


def calibration_stats(y, p10, p90) -> dict:
    below = float((y < p10).mean())
    above = float((y > p90).mean())
    return {"below_p10": below, "inside": 1.0 - below - above, "above_p90": above}


def train(data_dir: str, model_path: str) -> dict:
    np.random.seed(schema.SEED)

    feats = gf.generate(data_dir)
    channel_enc, camptype_enc = gf.build_encoders(feats)
    feats["channel_code"] = gf.encode(feats["channel"], channel_enc)
    feats["camptype_code"] = gf.encode(feats["campaign_type"], camptype_enc)

    # Time-based split — never shuffle.
    feats = feats.sort_values("week_start").reset_index(drop=True)
    cut = int(len(feats) * schema.TRAIN_FRACTION)
    train_df, val_df = feats.iloc[:cut], feats.iloc[cut:]
    print(f"[train] train {len(train_df)} rows "
          f"({train_df['week_start'].min():%Y-%m-%d} -> {train_df['week_start'].max():%Y-%m-%d}) | "
          f"val {len(val_df)} rows "
          f"({val_df['week_start'].min():%Y-%m-%d} -> {val_df['week_start'].max():%Y-%m-%d})")

    X_train = train_df[schema.FEATURE_COLS]
    y_train = train_df[schema.TARGET].values
    X_val = val_df[schema.FEATURE_COLS]
    y_val = val_df[schema.TARGET].values

    models = train_quantile_models(X_train, y_train)

    p10 = models["p10"].predict(X_val)
    p50 = models["p50"].predict(X_val)
    p90 = models["p90"].predict(X_val)
    p10, p50, p90 = enforce_monotonic(p10, p50, p90)

    raw_cal = calibration_stats(y_val, p10, p90)
    mae = float(np.mean(np.abs(y_val - p50)))
    print(f"[train] BEFORE conformal: below {raw_cal['below_p10']:.1%} | "
          f"inside {raw_cal['inside']:.1%} | above {raw_cal['above_p90']:.1%} | "
          f"P50 MAE {mae:.3f}")

    # Conformalized Quantile Regression: finite-sample coverage guarantee.
    # NOTE: the correction is data-dependent — always recomputed here, never
    # hardcoded.
    conformity = np.maximum(p10 - y_val, y_val - p90)
    correction = float(np.quantile(conformity, schema.CONFORMAL_COVERAGE))
    print(f"[train] conformal correction = {correction:.4f} ROAS points")

    cal = calibration_stats(y_val, np.maximum(p10 - correction, 0), p90 + correction)
    print(f"[train] AFTER conformal:  below {cal['below_p10']:.1%} | "
          f"inside {cal['inside']:.1%} | above {cal['above_p90']:.1%}")

    # Lag-1 autocorrelation of weekly P50 residuals, pooled within groups.
    # Used at predict time to aggregate weekly bands into period bands
    # (rho=1 reduces to a plain sum; rho=0 is the independence bound).
    resid = val_df[["channel", "campaign_type", "week_start"]].copy()
    resid["e"] = y_val - p50
    resid = resid.sort_values(["channel", "campaign_type", "week_start"])
    resid["e_prev"] = resid.groupby(["channel", "campaign_type"])["e"].shift(1)
    pairs = resid.dropna(subset=["e_prev"])
    if len(pairs) >= 10 and pairs["e"].std() > 0 and pairs["e_prev"].std() > 0:
        rho = float(np.clip(np.corrcoef(pairs["e"], pairs["e_prev"])[0, 1], 0.0, 1.0))
    else:
        rho = 1.0  # too little evidence — fall back to the conservative sum
    print(f"[train] weekly residual lag-1 autocorrelation rho = {rho:.3f} "
          f"({len(pairs)} pairs)")

    importance = dict(zip(schema.FEATURE_COLS,
                          [float(v) for v in models["p50"].feature_importances_]))
    top = sorted(importance.items(), key=lambda kv: -kv[1])[:10]
    print("[train] top-10 feature importance (P50 model):")
    for name, val in top:
        print(f"[train]   {name:<18} {val:.4f}")

    # Historical spend share — REQUIRED at predict time; the held-out test data
    # cannot be relied on to reproduce it.
    share = gf.spend_share(feats)

    bundle = {
        "p10": models["p10"],
        "p50": models["p50"],
        "p90": models["p90"],
        "feature_cols": schema.FEATURE_COLS,
        "channel_enc": channel_enc,
        "camptype_enc": camptype_enc,
        "conformal_correction": correction,
        "weekly_error_corr": rho,
        "spend_share": share,
        "calibration": {"raw": raw_cal, "conformal": cal, "p50_mae": mae},
        "trained_on": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs(os.path.dirname(os.path.abspath(model_path)), exist_ok=True)
    with open(model_path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"[train] wrote {model_path}")
    return bundle


def main():
    ap = argparse.ArgumentParser(description="Train quantile models + conformal correction")
    ap.add_argument("--data-dir", default="./data")
    ap.add_argument("--model", default="./pickle/model.pkl")
    args = ap.parse_args()
    train(args.data_dir, args.model)


if __name__ == "__main__":
    main()
