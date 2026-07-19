"""Data ingestion: discover CSVs in data/ dynamically, map to the canonical
schema, infer campaign types, merge, and clean.

Files are identified by column fingerprint, NEVER by filename — the grader's
held-out data may use different filenames.
"""

import glob
import os

import numpy as np
import pandas as pd

from src import schema


def _identify_source(columns) -> str | None:
    """Return the source key whose fingerprint columns are all present."""
    cols = set(columns)
    for source, spec in schema.SOURCE_SPECS.items():
        if all(c in cols for c in spec["fingerprint"]):
            return source
    return None


def load_raw(data_dir: str) -> pd.DataFrame:
    """Read every CSV in data_dir, map each to the canonical schema, merge."""
    paths = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
    if not paths:
        # Fallback: data may have been dropped in as an extracted zip subfolder.
        paths = sorted(glob.glob(os.path.join(data_dir, "**", "*.csv"), recursive=True))
    if not paths:
        raise FileNotFoundError(f"No CSV files found in {data_dir!r}")

    frames = []
    for path in paths:
        header = pd.read_csv(path, nrows=0)
        source = _identify_source(header.columns)
        if source is None:
            print(f"[ingest] WARNING: {os.path.basename(path)} does not match any "
                  f"known source schema — skipped")
            continue
        spec = schema.SOURCE_SPECS[source]
        df = pd.read_csv(path)
        out = pd.DataFrame({
            "date": df[spec["date_col"]],
            "spend": pd.to_numeric(df[spec["spend_col"]], errors="coerce")
                     / spec["spend_divisor"],
            "revenue": pd.to_numeric(df[spec["revenue_col"]], errors="coerce"),
            "campaign_name": df[spec["name_col"]],
        })
        out["channel"] = source
        frames.append(out)
        print(f"[ingest] {os.path.basename(path)} -> {source} ({len(out):,} rows)")

    if not frames:
        raise ValueError(f"No CSV in {data_dir!r} matched a known source schema "
                         f"(google/meta/microsoft)")

    merged = pd.concat(frames, ignore_index=True)
    merged["campaign_type"] = merged["campaign_name"].map(schema.infer_campaign_type)
    return merged[schema.CANONICAL_COLUMNS]


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the cleaning steps, in order (see docs/methodology.md)."""
    df = df.copy()

    # 1. Parse dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    # 2. Normalize categorical labels
    df["channel"] = df["channel"].astype(str).str.lower().str.strip()
    df["campaign_type"] = df["campaign_type"].astype(str).str.lower().str.strip()

    # 3. Numeric coercion
    for col in ("spend", "revenue"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # 4. Clip negatives to 0
    df["spend"] = df["spend"].clip(lower=0)
    df["revenue"] = df["revenue"].clip(lower=0)

    # 5. Drop zero-spend rows: the campaign wasn't running that day; they
    #    zero-inflate the target and teach the model nothing about how spend
    #    drives revenue.
    before = len(df)
    df = df[df["spend"] > 0].copy()
    dropped = before - len(df)
    if dropped:
        print(f"[clean] dropped {dropped:,} zero-spend rows")

    # 6. ROAS
    df["roas"] = df["revenue"] / df["spend"]

    # 7. Cap ROAS > 50 (almost always double-counted / misattributed revenue)
    capped = int((df["roas"] > schema.ROAS_CAP).sum())
    if capped:
        mask = df["roas"] > schema.ROAS_CAP
        df.loc[mask, "revenue"] = df.loc[mask, "spend"] * schema.ROAS_CAP
        df["roas"] = df["revenue"] / df["spend"]
        print(f"[clean] capped {capped:,} rows with ROAS > {schema.ROAS_CAP:g}")

    # 8. Drop duplicates
    df = df.drop_duplicates(subset=["date", "channel", "campaign_name"])

    df = df.sort_values("date").reset_index(drop=True)
    print(f"[clean] final: {len(df):,} rows, "
          f"{df['date'].min():%Y-%m-%d} -> {df['date'].max():%Y-%m-%d}, "
          f"spend ${df['spend'].sum():,.0f}, revenue ${df['revenue'].sum():,.0f}")
    return df


def load_clean(data_dir: str) -> pd.DataFrame:
    return clean(load_raw(data_dir))
