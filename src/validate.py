"""Campaign-consistency validation. Runs as step 1 of feature generation.

Separates HARD ERRORS (abort the pipeline) from WARNINGS (log and continue)
via a ValidationReport object. The scoring pipeline aborts on hard errors so
it never silently emits a bad predictions file.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src import schema


@dataclass
class ValidationReport:
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors

    def print_summary(self):
        print(f"[validate] {len(self.errors)} hard error(s), "
              f"{len(self.warnings)} warning(s)")
        for e in self.errors:
            print(f"[validate]   ERROR: {e}")
        for w in self.warnings:
            print(f"[validate]   warn : {w}")

    def raise_if_failed(self):
        if not self.ok:
            raise ValueError(
                "Validation failed with hard errors:\n  - " + "\n  - ".join(self.errors)
            )


def validate(raw: pd.DataFrame) -> ValidationReport:
    """Validate the merged canonical table (pre-cleaning)."""
    rep = ValidationReport()

    # --- Schema & types -----------------------------------------------------
    missing = [c for c in schema.CANONICAL_COLUMNS if c not in raw.columns]
    if missing:
        rep.error(f"missing canonical columns: {missing}")
        rep.print_summary()
        return rep

    if raw.empty:
        rep.error("input data is empty")
        rep.print_summary()
        return rep

    dates = pd.to_datetime(raw["date"], errors="coerce")
    n_bad_dates = int(dates.isna().sum())
    if n_bad_dates == len(raw):
        rep.error("no parseable dates in the data")
    elif n_bad_dates:
        rep.warn(f"{n_bad_dates:,} rows with unparseable dates (will be dropped)")

    spend = pd.to_numeric(raw["spend"], errors="coerce")
    revenue = pd.to_numeric(raw["revenue"], errors="coerce")
    for name, s in (("spend", spend), ("revenue", revenue)):
        n = int(s.isna().sum())
        if n:
            rep.warn(f"{n:,} non-numeric {name} values (coerced to 0)")

    # --- Business logic -----------------------------------------------------
    n_neg_spend = int((spend < 0).sum())
    if n_neg_spend:
        rep.error(f"{n_neg_spend:,} rows with negative spend — data corruption")

    n_neg_rev = int((revenue < 0).sum())
    if n_neg_rev:
        rep.warn(f"{n_neg_rev:,} rows with negative revenue (zeroed)")

    df = raw.assign(date=dates, spend=spend.fillna(0), revenue=revenue.fillna(0))
    df = df.dropna(subset=["date"])
    active = df[df["spend"] > 0]

    if not active.empty:
        roas = active["revenue"] / active["spend"]
        n_high = int((roas > schema.ROAS_CAP).sum())
        if n_high:
            rep.warn(f"{n_high:,} rows with ROAS > {schema.ROAS_CAP:g} "
                     f"(likely tracking error — capped downstream)")
        pct_zero_rev = 100.0 * float((active["revenue"] == 0).mean())
        if pct_zero_rev > 20:
            rep.warn(f"{pct_zero_rev:.1f}% of active rows have spend>0 but revenue=0")

    # WoW spend spikes (>=5x) at channel/campaign_type weekly grain
    wk = df.copy()
    wk["week_start"] = wk["date"].dt.to_period("W").dt.start_time
    wspend = (wk.groupby(["channel", "campaign_type", "week_start"])["spend"]
                .sum().reset_index().sort_values("week_start"))
    prev = wspend.groupby(["channel", "campaign_type"])["spend"].shift(1)
    spikes = int(((wspend["spend"] >= 5 * prev) & (prev > 0)).sum())
    if spikes:
        rep.warn(f"{spikes:,} channel/campaign-type weeks show >=5x WoW spend spike")

    # --- Campaign continuity ------------------------------------------------
    overall_min, overall_max = df["date"].min(), df["date"].max()
    camp = df.groupby(["channel", "campaign_name"])["date"].agg(["min", "max", "nunique"])
    camp["span_days"] = (camp["max"] - camp["min"]).dt.days + 1
    camp["gap_days"] = camp["span_days"] - camp["nunique"]
    gappy = camp[camp["gap_days"] > 30]
    if len(gappy):
        rep.warn(f"{len(gappy)} campaigns with >30 internal gap days "
                 f"(pause or rename candidates)")
    late = camp[camp["min"] > overall_min + pd.Timedelta(days=90)]
    if len(late):
        rep.warn(f"{len(late)} campaigns started >90 days after the data begins")
    early = camp[camp["max"] < overall_max - pd.Timedelta(days=90)]
    if len(early):
        rep.warn(f"{len(early)} campaigns ended >90 days before the data ends")

    # --- Temporal completeness & cross-channel alignment --------------------
    total_days = (overall_max - overall_min).days + 1
    if total_days < 8 * 7:
        rep.error(f"only {total_days} days of history — need at least "
                  f"{schema.MIN_WEEKS} weeks to build features")

    for ch, g in df.groupby("channel"):
        ch_min, ch_max = g["date"].min(), g["date"].max()
        present = g["date"].dt.normalize().nunique()
        expected = (ch_max - ch_min).days + 1
        missing_days = expected - present
        if missing_days > 0:
            rep.warn(f"channel '{ch}' missing {missing_days} calendar days "
                     f"between {ch_min:%Y-%m-%d} and {ch_max:%Y-%m-%d}")
        if (ch_min > overall_min + pd.Timedelta(days=30)
                or ch_max < overall_max - pd.Timedelta(days=30)):
            rep.warn(f"channel '{ch}' covers {ch_min:%Y-%m-%d} -> {ch_max:%Y-%m-%d}, "
                     f"misaligned with overall range "
                     f"{overall_min:%Y-%m-%d} -> {overall_max:%Y-%m-%d}")

    rep.print_summary()
    return rep
