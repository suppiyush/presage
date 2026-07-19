# Presage - Probabilistic Revenue & ROAS Forecasting

**Parity Check - LNMIIT Jaipur**

A forecasting tool for digital marketing agencies. It takes ad spend data from Google, Meta, and Microsoft, and predicts future revenue and ROAS (Return on Ad Spend) for the next 30, 60, or 90 days. Instead of giving a single number, it gives a range (a low estimate, a middle estimate, and a high estimate) so you know how uncertain the forecast is. It can also simulate what happens if you change your budget and suggest how to split spend across channels.

---

## Quick start (scoring pipeline)

Python **3.12** (developed and tested on 3.12; all versions pinned in `requirements.txt`).

```bash
git clone <this-repo>
cd aignition-forecasting

# Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
./run.sh ./data ./pickle/model.pkl ./output/predictions.csv
# or with defaults:
bash run.sh
```

`run.sh` accepts three positional args `(DATA_DIR, MODEL_PATH, OUTPUT_PATH)` with the defaults above. It runs feature generation and prediction in one shot using the pre-trained model at `pickle/model.pkl`. No retraining, no network calls, no prompts, no absolute paths. CSVs in `data/` are discovered dynamically and identified by column fingerprint, never by filename.

## Retraining (after replacing `data/`)

```bash
python -m src.train --data-dir ./data --model ./pickle/model.pkl
```

Prints the calibration report (before/after conformal correction) and rewrites the pickle. The conformal correction and spend shares are recomputed from the data; nothing is hardcoded.

## Demo dashboard (React + FastAPI)

```bash
pip install -r requirements.txt -r requirements-demo.txt
cd frontend && npm install && npm run build && cd ..
uvicorn backend.app.main:app --port 8000
# open http://localhost:8000
```

Frontend development (hot reload; proxies /api to :8000):

```bash
cd frontend && npm run dev
```

Routes: `/` is the landing page, `/dashboard` is the forecasting dashboard.

Optional (for LLM narratives; the app works with zero keys via a template fallback). Put keys in a `.env` at the repo root (gitignored, see `.env.example`) or export them:

```bash
export GEMINI_API_KEY="..."   # aistudio.google.com (primary)
export HF_TOKEN="hf_..."      # huggingface.co/settings/tokens (secondary)
```

## Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

Covers: quantile monotonicity, non-negativity, uncertainty widening with horizon, output schema + fresh-write, conformal calibration (~10/80/10), filename-agnostic ingestion, no network access in the scoring path, and clean unpickling.

## What's inside

| Path                       | Role                                                                      |
| -------------------------- | ------------------------------------------------------------------------- |
| `run.sh`                   | Scoring entry point (feature gen + predict, one shot)                     |
| `src/schema.py`            | Single source of truth: I/O columns, constants, model config              |
| `src/ingest.py`            | Dynamic CSV discovery, column mapping, cleaning                           |
| `src/validate.py`          | Hard-error vs warning validation report                                   |
| `src/generate_features.py` | Weekly aggregation + 19-feature table                                     |
| `src/train.py`             | 3 quantile XGBoost models + conformal correction to pickle                |
| `src/predict.py`           | Horizon forecasts to `predictions.csv`                                    |
| `src/budget_sim.py`        | Response curves + SLSQP optimal allocation                                |
| `src/anomaly.py`           | ROAS anomaly & regime-shift detection                                     |
| `src/ai_narrative.py`      | LLM causal summaries (demo path only, never in scoring)                   |
| `backend/`                 | FastAPI app: routers, services, model store (demo path only)              |
| `frontend/`                | React + TypeScript site (Vite + Tailwind): landing + dashboard            |
| `docs/`                    | [Methodology](docs/methodology.md) - [Architecture](docs/architecture.md) |

## How it works

Ad data is grouped into **weekly buckets** per channel and campaign type. Weekly aggregation smooths out day-to-day noise and gives the model stable patterns to learn from. Features include planned spend, recent spend history (lags and rolling averages), and calendar signals like holidays and seasonality.

The model predicts **ROAS** (not revenue directly) using three XGBoost models trained on different quantiles. Revenue is then derived as spend x predicted ROAS. The three quantiles give you:

- **P10**: the pessimistic estimate. Only 10% of outcomes are expected to be worse than this.
- **P50**: the median estimate. The most likely outcome.
- **P90**: the optimistic estimate. Only 10% of outcomes are expected to be better than this.

Together, P10 and P90 form an 80% confidence band. Raw quantile models tend to produce bands that are too narrow, so we apply **conformal calibration**: a statistical correction that widens the band just enough so it covers the true outcome the right percentage of the time.

Because spend is a model input, we can vary it to generate budget-response curves and find the allocation that maximizes expected ROAS across channels.

> **Note on `data/`:** the committed folder contains the real campaign CSVs (Google, Meta, Bing) that the model is trained on. The grader overwrites this folder with held-out data and re-runs the pipeline via `run.sh`.

## Honest limitations

- Multi-step forecasts are **recursive**: each future week's lag/rolling features come from the model's own P50 path, so weekly forecasts evolve instead of staying flat. P10/P90 are predicted conditional on that median path, and weekly bands are calibrated one-step-ahead. Full uncertainty propagation through the recursion is the remaining next step.
- Period bands aggregate weekly quantiles using the empirically estimated week-to-week residual correlation rather than a plain sum. A plain sum assumes perfectly correlated weeks and overstates the band. Cross-group rollups (channel/aggregate rows) still use plain sums, which is the conservative direction.
- The optimizer is confined to +/-40% of the current plan. Outside historically observed spend, the model extrapolates and its claims are not trustworthy.
