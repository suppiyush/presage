"""Application settings.

Paths are resolved relative to the repository root so the server can be
started from anywhere with `uvicorn backend.app.main:app`.
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]

_env_origins = os.environ.get("CORS_ORIGINS", "")


class Settings:
    model_path: str = str(REPO_ROOT / "pickle" / "model.pkl")
    data_dir: str = str(REPO_ROOT / "data")
    frontend_dist: Path = REPO_ROOT / "dashboard" / "frontend" / "dist"

    # In production set CORS_ORIGINS to a comma-separated list of allowed origins
    # (e.g. the Vercel frontend URL). Falls back to the Vite dev server.
    cors_origins: list[str] = (
        [o.strip() for o in _env_origins.split(",") if o.strip()]
        if _env_origins
        else ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    trailing_weeks: int = 4  # window used for "recent actuals" comparisons


settings = Settings()
