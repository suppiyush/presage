# Methodology

## 1. Data ingestion & canonical mapping

CSVs in `data/` are discovered by glob and identified by **column fingerprint**
(e.g. `metrics_cost_micros` ⇒ Google), never by filename — the held-out test
set may be named differently. Each source maps to a canonical table
`(date, channel, campaign_type, campaign_name, spend, revenue)`:

| Canonical | Google | Meta | Microsoft (Bing) |
|---|---|---|---|
| date | `segments_date` | `date_start` | `TimePeriod` |
| spend | `metrics_cost_micros / 1e6` | `spend` | `Spend` |
| revenue | `metrics_conversions_value` | `conversion` | `Revenue` |

Two empirically-verified gotchas are baked in:

1. **Google spend is in micros** — divided by 1,000,000.
2. **Meta's `conversion` column is revenue, not a count.** Its values are
   dollar-scale decimals; treating them as revenue yields a normal ~2x ROAS,
   treating them as counts is nonsense. No AOV estimation is needed.

Campaign type is inferred from the campaign name for all three channels
(consistent labels), using ordered pattern checks (`TM` = trademark = brand,
`NTM` = non-brand, plus remarketing/prospecting/shopping/demand gen/display/
video/pmax/search/generic). Bing's `CampaignType` column is deliberately
ignored in favour of the same name-based inference.

## 2. Cleaning (in order)

1. Parse dates; drop unparseable rows.
2. Lowercase/strip categorical labels.
3. Coerce `spend`/`revenue` to numeric, NaN → 0.
4. Clip negatives to 0.
5. **Drop zero-spend rows** — the campaign wasn't running; they zero-inflate
   the target and teach the model nothing about how spend drives revenue.
6. Compute `roas = revenue / spend`.
7. **Cap ROAS at 50** (set revenue = spend × 50). ROAS beyond 50 is almost
   always double-counted or misattributed revenue; leaving it in makes the
   model wildly overoptimistic.
8. Drop duplicates on `(date, channel, campaign_name)`.

Validation (`src/validate.py`) runs before cleaning and separates **hard
errors** (missing columns, empty data, negative spend, insufficient history →
abort) from **warnings** (ROAS>50 counts, zero-revenue share, WoW spend
spikes, campaign gaps, channel coverage misalignment → log and continue).

## 3. Feature engineering

- **Daily → weekly** aggregation per `(channel, campaign_type)`: daily data is
  too noisy and zero-inflated; weekly smooths it.
- Groups with **< 8 weeks** of history are dropped (too sparse to learn).
- **Target = ROAS, not revenue.** ROAS is far more stationary → calibrates
  better; revenue is recovered as `spend × predicted ROAS`; and because spend
  is an **input feature**, sweeping it yields budget-response curves — pure
  time-series models (Prophet/ARIMA) have no spend dimension and structurally
  cannot do budget simulation.
- 19 features: planned spend; 1w/4w revenue lags; 1w spend & ROAS lags;
  4-week rolling means of revenue/spend/ROAS (always `shift(1)` **before**
  rolling — no leakage); month/quarter/week-of-year; US-holiday-week and BFCM
  flags; yearly + half-yearly Fourier terms; label-encoded channel and
  campaign type.

## 4. Model

Three XGBoost quantile regressors (`reg:quantileerror`, α = 0.10/0.50/0.90),
identical hyperparameters (300 trees, depth 4, lr 0.05, subsample 0.8,
colsample 0.8, min_child_weight 3, seed 42). **One model per quantile, not per
channel** — channel and campaign type are features.

Split is **time-based at 85%**, never shuffled: the validation window is the
most recent ~15% of weeks.

After every prediction: `p10 = min(p10, p50)`, `p90 = max(p90, p50)`,
all clipped at 0.

## 5. Conformal calibration (CQR)

Raw quantile regression gives *approximate* quantiles with no coverage
guarantee — our raw band under-covered. Conformalized Quantile Regression
repairs this with a finite-sample guarantee:

```
conformity = max(p10 − y, y − p90)         (on the validation window)
correction = quantile(conformity, 0.80)
p10 ← p10 − correction ;  p90 ← p90 + correction
```

The correction is **data-dependent and recomputed by `train.py`** every run,
then stored in the model bundle and applied at every prediction. On the
reference dataset this moved coverage from ~64% to ~80% (nominal 80%).

## 6. Forecast generation

Horizons are **relative to the last date in the data** (30d = 4 weeks,
60d = 9, 90d = 13) — never a hardcoded calendar month.

Forecasting is **recursive** (multi-step "recursive strategy"): each group
keeps a trajectory buffer seeded from its last 4 observed weeks. Weeks are
predicted one at a time (batched across groups); after each week the model's
P50 outcome (`revenue = spend × roas_p50`) is appended to the buffer, so the
next week's lag/rolling features evolve with the forecast instead of staying
frozen. P10/P90 are predicted conditional on that single median path —
recursing each quantile on its own path would compound quantiles and inflate
the band. XGBoost trees cannot predict outside the target range seen in
training, so the feedback loop is bounded.

Per week: apply conformal correction and monotonicity; `revenue_q = spend ×
roas_q`. **Period bands** then aggregate weekly bands with the empirically
estimated week-to-week residual correlation ρ (lag-1 autocorrelation of P50
validation residuals, pooled within groups, stored in the bundle as
`weekly_error_corr`):

```
d_i  = weekly half-band (P50−P10 below, P90−P50 above)
half = sqrt( ρ·(Σ d_i)² + (1−ρ)·Σ d_i² )
```

ρ=1 reduces to a plain sum (perfect correlation — the old behaviour and the
fallback for bundles without the field); ρ=0 is the independence bound. On the
reference data ρ ≈ 0.20, tightening period bands substantially while keeping
them strictly widening with horizon. Cross-group rollups (channel/aggregate
rows) still use plain sums — the conservative direction.

### Budget allocation by historical spend share — the critical fix

Splitting a channel's budget **evenly** across its campaign types is an
unrealistic scenario: it funds near-zero-ROAS awareness types (display/video)
at the expense of the workhorses, and the (correct!) model then predicts the
resulting bad revenue. Allocation must follow the **historical spend share**
of each campaign type within its channel (computed via a merge of type totals
against channel totals, persisted in the model bundle — held-out data cannot
be relied on to reproduce it). Types with zero share are skipped. On the
reference data this single fix moved the 30-day P50 from an implausible
2.75x blended ROAS to 4.04x — within 1% of actual trailing-30-day revenue.

**Uncertainty must widen with horizon** — the P90−P10 band at 90d > 60d > 30d.
This is asserted in the test suite.

## 7. Budget simulator & optimizer

Response curves sweep each channel's budget 50% → 200% of plan (15 points),
re-forecasting at each level — exposing diminishing returns / saturation.

The allocator (`scipy.optimize.minimize`, SLSQP) maximizes total P50 revenue
subject to a fixed total budget, with **symmetric ±40% bounds** around the
current plan. Two failure modes motivated the bounds, both observed:

- **Extrapolation blowup:** with loose bounds the optimizer pushed ~30×
  historical spend into the smallest channel, claiming +20% revenue — the
  model had never seen that spend level; the claim is garbage.
- **Asymmetric-bound negative lift:** bounding by historical min/max capped a
  strong channel *below* its current spend, forcing money into weak channels
  and producing negative lift.

A small available lift is reported honestly as "the current mix is
near-optimal" — the tool's ongoing value is regime-change monitoring, not
one-off reallocation.

## 8. Anomaly detection

Weekly blended ROAS per channel is scanned against an 8-week rolling mean;
deviations beyond 1.5σ are flagged with structured records. A separate
regime-shift detector compares trailing-4-week ROAS to the long-run average
and flags divergences ≥35% — this is what surfaces a silent channel
efficiency collapse automatically.

## 9. Honest limitations

- **Weekly bands are calibrated one-step-ahead**; the recursion conditions
  P10/P90 on the median path but does not propagate multi-step uncertainty
  through the lag features themselves. Rolling-origin CV with per-step
  conformal corrections is the natural next step.
- **Period bands are correlation-adjusted, not exact**: ρ is a single pooled
  lag-1 estimate, and cross-group rollups (channel/aggregate rows) still use
  plain sums (conservative).
- **Spend shares are assumed stable** over the horizon; a deliberate mix
  change by the advertiser invalidates the allocation assumption (the
  simulator exists precisely to explore such scenarios).
