"""Model store: loads the trained bundle and feature table once at startup
and memoizes the expensive derived computations (curves, optimizer runs).

The store is the only place that touches `src/` — services consume it.
"""

import sys
from pathlib import Path

# Add the backend root to sys.path so `src.*` resolves from backend/src/.
_BACKEND_ROOT = str(Path(__file__).resolve().parents[2])
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

import pandas as pd  # noqa: E402

from src import anomaly, budget_sim, schema  # noqa: E402
from src.generate_features import generate  # noqa: E402
from src.predict import derive_budget_plan, forecast_groups, load_bundle  # noqa: E402


class ModelStore:
    def __init__(self, model_path: str, data_dir: str):
        self._model_path = model_path
        self._data_dir = data_dir
        self.bundle = None
        self.feats: pd.DataFrame | None = None
        self._default_plans: dict[int, dict[str, float]] = {}
        self._curves: dict[tuple, pd.DataFrame] = {}
        self._optimizers: dict[tuple, dict] = {}

    # -- lifecycle -----------------------------------------------------------

    def load(self) -> None:
        self.bundle = load_bundle(self._model_path)
        self.feats = generate(self._data_dir)

    # -- static facts --------------------------------------------------------

    @property
    def horizons(self) -> list[int]:
        return list(schema.HORIZONS_DAYS)

    @property
    def channels(self) -> list[str]:
        return sorted(self.feats["channel"].unique())

    @property
    def calibration(self) -> dict:
        return self.bundle["calibration"]["conformal"]

    @property
    def last_data_date(self) -> str:
        return str(pd.Timestamp(self.feats["week_start"].max()).date())

    # -- memoized derivations ------------------------------------------------

    def default_plan(self, horizon: int) -> dict[str, float]:
        if horizon not in self._default_plans:
            self._default_plans[horizon] = derive_budget_plan(self.feats, horizon)
        return self._default_plans[horizon]

    def forecast(self, horizon: int, plan: dict[str, float] | None = None) -> pd.DataFrame:
        return forecast_groups(self.bundle, self.feats, horizon, plan)

    @staticmethod
    def _plan_key(horizon: int, plan: dict[str, float] | None) -> tuple:
        if plan is None:
            return (horizon, None)
        return (horizon, tuple(sorted((ch, round(v)) for ch, v in plan.items())))

    def response_curves(self, horizon: int,
                        plan: dict[str, float] | None = None) -> pd.DataFrame:
        key = self._plan_key(horizon, plan)
        if key not in self._curves:
            self._curves[key] = budget_sim.response_curves(
                self.bundle, self.feats, horizon, budget_plan=plan)
        return self._curves[key]

    def optimizer(self, horizon: int, plan: dict[str, float] | None = None) -> dict:
        key = self._plan_key(horizon, plan)
        if key not in self._optimizers:
            self._optimizers[key] = budget_sim.optimize_allocation(
                self.bundle, self.feats, horizon, budget_plan=plan)
        return self._optimizers[key]

    def regime_shifts(self) -> pd.DataFrame:
        return anomaly.detect_regime_shifts(self.feats)

    def weekly_anomalies(self) -> pd.DataFrame:
        return anomaly.detect_anomalies(self.feats)

    def weekly_channel_roas(self) -> pd.DataFrame:
        wk = (self.feats.groupby(["channel", "week_start"], as_index=False)
              [["spend", "revenue"]].sum())
        wk["roas"] = wk["revenue"] / wk["spend"]
        return wk

    def trailing_actuals(self, weeks: int) -> dict[str, float]:
        wk = (self.feats.groupby("week_start")[["spend", "revenue"]]
              .sum().sort_index().tail(weeks).sum())
        spend, revenue = float(wk["spend"]), float(wk["revenue"])
        return {"spend": spend, "revenue": revenue,
                "roas": revenue / spend if spend else 0.0}
