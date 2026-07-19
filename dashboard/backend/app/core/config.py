"""Application settings.

Paths are resolved relative to the repository root so the server can be
started from anywhere with `uvicorn backend.app.main:app`.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings:
    model_path: str = str(REPO_ROOT / "pickle" / "model.pkl")
    data_dir: str = str(REPO_ROOT / "data")
    frontend_dist: Path = REPO_ROOT / "dashboard" / "frontend" / "dist"

    # Vite dev server origin (CORS is only needed during development;
    # in production the API serves the built frontend from the same origin).
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    trailing_weeks: int = 4  # window used for "recent actuals" comparisons


settings = Settings()
