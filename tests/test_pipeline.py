"""End-to-end pipeline tests (Part 13 of the build contract).

Run:  python -m pytest tests/ -v
Requires the sample data in data/ and the trained pickle in pickle/model.pkl.
"""

import glob
import os
import shutil
import socket
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import schema                                   # noqa: E402
from src.generate_features import generate               # noqa: E402
from src.predict import (build_predictions, forecast_groups,  # noqa: E402
                         load_bundle)

DATA_DIR = os.path.join(ROOT, "data")
MODEL_PATH = os.path.join(ROOT, "pickle", "model.pkl")


@pytest.fixture(scope="session")
def bundle():
    return load_bundle(MODEL_PATH)


@pytest.fixture(scope="session")
def feats():
    return generate(DATA_DIR)


@pytest.fixture(scope="session")
def preds(bundle, feats):
    return build_predictions(bundle, feats)


# 1. Quantile monotonicity ---------------------------------------------------

def test_monotonic_quantiles(preds):
    assert (preds["revenue_p10"] <= preds["revenue_p50"] + 1e-9).all()
    assert (preds["revenue_p50"] <= preds["revenue_p90"] + 1e-9).all()
    assert (preds["roas_p10"] <= preds["roas_p50"] + 1e-9).all()
    assert (preds["roas_p50"] <= preds["roas_p90"] + 1e-9).all()


# 2. Non-negativity ----------------------------------------------------------

def test_non_negative(preds):
    value_cols = [c for c in schema.OUTPUT_COLUMNS if c.startswith(("revenue", "roas"))]
    assert (preds[value_cols] >= 0).all().all()


# 3. Uncertainty widens with horizon ------------------------------------------

def test_band_width_increases_with_horizon(preds):
    agg = preds[(preds["channel"] == schema.AGGREGATE_LABEL)
                & (preds["campaign_type"] == schema.AGGREGATE_LABEL)]
    agg = agg.sort_values("horizon_days")
    widths = (agg["revenue_p90"] - agg["revenue_p10"]).values
    assert len(widths) == len(schema.HORIZONS_DAYS)
    assert all(widths[i] < widths[i + 1] for i in range(len(widths) - 1)), \
        f"P90-P10 band must widen with horizon, got {widths}"


# 4. Output schema & fresh write ----------------------------------------------

def test_output_schema_and_fresh_write(preds, tmp_path):
    assert list(preds.columns) == schema.OUTPUT_COLUMNS
    # every horizon has an aggregate row
    agg = preds[(preds["channel"] == schema.AGGREGATE_LABEL)
                & (preds["campaign_type"] == schema.AGGREGATE_LABEL)]
    assert sorted(agg["horizon_days"].tolist()) == sorted(schema.HORIZONS_DAYS)

    out = tmp_path / "predictions.csv"
    preds.to_csv(out, index=False)
    preds.to_csv(out, index=False)  # second write must overwrite, not append
    back = pd.read_csv(out)
    assert len(back) == len(preds)
    assert list(back.columns) == schema.OUTPUT_COLUMNS


# 5. Calibration after conformal correction -----------------------------------

def test_calibration(bundle):
    cal = bundle["calibration"]["conformal"]
    assert abs(cal["inside"] - schema.CONFORMAL_COVERAGE) <= 0.05, \
        f"inside-band coverage {cal['inside']:.1%} not within ±5pp of 80%"
    # tails are individually looser: CQR guarantees total coverage, not symmetry
    assert 0.02 <= cal["below_p10"] <= 0.18
    assert 0.02 <= cal["above_p90"] <= 0.18


# 6. Pipeline is filename-agnostic ---------------------------------------------

def test_runs_with_renamed_files_and_fewer_rows(bundle, tmp_path):
    for i, path in enumerate(sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))):
        df = pd.read_csv(path)
        df = df.iloc[: int(len(df) * 0.8)]  # different row counts than committed
        df.to_csv(tmp_path / f"holdout_file_{i}.csv", index=False)

    feats2 = generate(str(tmp_path))
    preds2 = build_predictions(bundle, feats2)
    assert len(preds2) > 0
    assert list(preds2.columns) == schema.OUTPUT_COLUMNS


# 7. No network access in the scoring path -------------------------------------

def test_no_network_in_scoring_path(bundle, monkeypatch):
    def _deny(*args, **kwargs):
        raise AssertionError("network access attempted in scoring path")

    monkeypatch.setattr(socket, "socket", _deny)
    monkeypatch.setattr(socket, "create_connection", _deny)

    feats3 = generate(DATA_DIR)
    preds3 = build_predictions(bundle, feats3)
    assert len(preds3) > 0

    # and the scoring modules must not import the LLM module
    scoring_sources = ["ingest.py", "validate.py", "generate_features.py",
                       "train.py", "predict.py", "schema.py"]
    for fname in scoring_sources:
        with open(os.path.join(ROOT, "src", fname), encoding="utf-8") as f:
            assert "ai_narrative" not in f.read(), \
                f"src/{fname} must never import ai_narrative"


# 8. Model unpickles and predicts in this env ----------------------------------

def test_model_unpickles_and_predicts(bundle):
    for key in ("p10", "p50", "p90", "feature_cols", "channel_enc",
                "camptype_enc", "conformal_correction", "spend_share"):
        assert key in bundle, f"bundle missing {key}"
    X = pd.DataFrame([{c: 1.0 for c in bundle["feature_cols"]}])
    for q in ("p10", "p50", "p90"):
        pred = bundle[q].predict(X)
        assert np.isfinite(pred).all()


# 9. Recursive forecasting: weekly P50 paths evolve, they are not flat ---------

def test_recursive_weekly_path_not_flat(bundle, feats):
    weekly = forecast_groups(bundle, feats, 90, return_weekly=True)
    n_flat = 0
    for (_, _), g in weekly.groupby(["channel", "campaign_type"]):
        if g["revenue_p50"].nunique() <= 1:
            n_flat += 1
    # With recursive lags + calendar features, flat paths should be rare
    # (a group pinned at ROAS 0 every week can legitimately be flat).
    n_groups = weekly.groupby(["channel", "campaign_type"]).ngroups
    assert n_flat <= n_groups * 0.3, \
        f"{n_flat}/{n_groups} groups have a constant weekly P50 path"


# 10. Period bands sit between the independence and perfect-correlation bounds -

def test_period_band_between_independence_and_sum(bundle, feats):
    rho = bundle.get("weekly_error_corr", 1.0)
    assert 0.0 <= rho <= 1.0

    weekly = forecast_groups(bundle, feats, 90, return_weekly=True)
    period = forecast_groups(bundle, feats, 90)

    d_low = (weekly["revenue_p50"] - weekly["revenue_p10"]).clip(lower=0)
    weekly = weekly.assign(d_low=d_low, d_low_sq=d_low ** 2)
    bounds = weekly.groupby(["channel", "campaign_type"], as_index=False).agg(
        d_sum=("d_low", "sum"), d_sq=("d_low_sq", "sum"))
    bounds["indep"] = np.sqrt(bounds["d_sq"])

    merged = period.merge(bounds, on=["channel", "campaign_type"])
    half_low = merged["revenue_p50"] - merged["revenue_p10"]
    eps = 1e-6
    # <= sum bound always; >= independence bound unless clipped at zero revenue
    assert (half_low <= merged["d_sum"] + eps).all()
    unclipped = merged["revenue_p10"] > 0
    assert (half_low[unclipped] >= merged["indep"][unclipped] - eps).all()
