"""Single source of truth for I/O columns, constants and model config.

Everything that defines "what the pipeline reads and writes" lives here so a
format change (e.g. the official predictions.csv spec) is a one-file edit.

TODO(CRITICAL): OUTPUT_COLUMNS below is our proposed schema. Verify it against
the official launch doc / organizer email BEFORE submitting. Right answers in
the wrong format score zero.
"""

# ---------------------------------------------------------------------------
# Output contract (predictions.csv)
# ---------------------------------------------------------------------------

OUTPUT_COLUMNS = [
    "channel",
    "campaign_type",
    "horizon_days",
    "revenue_p10",
    "revenue_p50",
    "revenue_p90",
    "roas_p10",
    "roas_p50",
    "roas_p90",
]

# Value used for roll-up rows (channel-level and grand-total rows).
AGGREGATE_LABEL = "ALL"

HORIZONS_DAYS = [30, 60, 90]

# ---------------------------------------------------------------------------
# Input contract (data/ folder)
# ---------------------------------------------------------------------------
# Files are discovered dynamically (glob *.csv) and identified by a column
# fingerprint, never by filename. Each source maps to the canonical schema:
# date, spend, revenue, campaign_name, channel.

SOURCE_SPECS = {
    "google": {
        # Columns that positively identify a Google Ads export.
        "fingerprint": ["metrics_cost_micros", "segments_date"],
        "date_col": "segments_date",
        "spend_col": "metrics_cost_micros",
        "spend_divisor": 1_000_000.0,  # cost is in MICROS
        "revenue_col": "metrics_conversions_value",
        "name_col": "campaign_name",
    },
    "meta": {
        "fingerprint": ["date_start", "spend"],
        "date_col": "date_start",
        "spend_col": "spend",
        "spend_divisor": 1.0,
        # Meta's `conversion` column IS revenue (verified empirically),
        # not a conversion count.
        "revenue_col": "conversion",
        "name_col": "campaign_name",
    },
    "microsoft": {
        "fingerprint": ["TimePeriod", "Spend"],
        "date_col": "TimePeriod",
        "spend_col": "Spend",
        "spend_divisor": 1.0,
        "revenue_col": "Revenue",
        "name_col": "CampaignName",
    },
}

CANONICAL_COLUMNS = ["date", "channel", "campaign_type", "campaign_name", "spend", "revenue"]

# ---------------------------------------------------------------------------
# Cleaning / feature-engineering constants
# ---------------------------------------------------------------------------

ROAS_CAP = 50.0        # ROAS above this is treated as a tracking error and capped
MIN_WEEKS = 8          # groups with less weekly history than this are dropped
LAG_WEEKS = 1
ROLL_WEEKS = 4

FEATURE_COLS = [
    "spend",
    "revenue_lag_1w",
    "revenue_lag_4w",
    "spend_lag_1w",
    "roas_lag_1w",
    "revenue_roll_4w",
    "spend_roll_4w",
    "roas_roll_4w",
    "month",
    "quarter",
    "week_of_year",
    "is_holiday_week",
    "is_bfcm",
    "sin_52",
    "cos_52",
    "sin_26",
    "cos_26",
    "channel_code",
    "camptype_code",
]
TARGET = "roas"

# ---------------------------------------------------------------------------
# Model config
# ---------------------------------------------------------------------------

SEED = 42
QUANTILES = {"p10": 0.10, "p50": 0.50, "p90": 0.90}
TRAIN_FRACTION = 0.85          # time-based split, never shuffled
CONFORMAL_COVERAGE = 0.80      # nominal coverage of the P10-P90 band

XGB_PARAMS = dict(
    objective="reg:quantileerror",
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=3,
    random_state=SEED,
    n_jobs=-1,
)

# ---------------------------------------------------------------------------
# Budget optimizer guardrails (see docs/methodology.md)
# ---------------------------------------------------------------------------

# Symmetric bounds around the current plan. Asymmetric/historical bounds
# produce invalid results (extrapolation blowups or forced negative lift).
OPTIMIZER_BOUND_LOW = 0.60
OPTIMIZER_BOUND_HIGH = 1.40


def infer_campaign_type(name) -> str:
    """Infer campaign type from its name. Order matters: specific first.

    TM = Trademark = brand; NTM = Non-Trademark = non-brand.
    """
    n = str(name).lower()
    if "remarketing" in n:
        return "remarketing"
    if "prospecting" in n:
        return "prospecting"
    if "shopping" in n:
        return "shopping"
    if "demand gen" in n:
        return "demand_gen"
    if "display" in n:
        return "display"
    if "video" in n:
        return "video"
    if "pmax" in n:
        return "pmax"
    if "_tm_" in n:
        return "brand"
    if "_ntm_" in n:
        return "non-brand"
    if "search" in n:
        return "search"
    if "generic" in n:
        return "generic"
    return "other"
