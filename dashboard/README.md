# Dashboard

React + FastAPI dashboard for the Presage forecasting system. The frontend talks to the backend API during development; in production the API serves the built frontend from the same origin.

## Structure

```
dashboard/
├── backend/   FastAPI app — loads the model bundle and exposes /api routes
└── frontend/  React (Vite + TypeScript + Tailwind) SPA
```

## Backend

### Setup

```bash
cd dashboard
pip install -r backend/requirements.txt
```

Set any optional env vars before starting:

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Enables Gemini-powered AI narratives (primary) |
| `HF_TOKEN` | Fallback HF Inference API narratives |

If neither is set the narrative endpoint returns a rule-based template — no network required.

### Run

```bash
cd dashboard
uvicorn backend.app.main:app --port 8000
```

API is available at `http://localhost:8000/api`. Interactive docs at `http://localhost:8000/docs`.

## Frontend

### Setup

```bash
cd dashboard/frontend
npm install
```

### Dev server

```bash
npm run dev
```

Runs at `http://localhost:5173`. Proxies `/api` requests to the backend at port 8000.

### Production build

```bash
npm run build
```

Outputs to `frontend/dist/`. Once built, the backend serves the SPA at `/` — no separate frontend server needed.

## Running both together (development)

Open two terminals:

```bash
# Terminal 1 — API
cd dashboard
uvicorn backend.app.main:app --port 8000 --reload

# Terminal 2 — UI
cd dashboard/frontend
npm run dev
```

Open `http://localhost:5173`.
