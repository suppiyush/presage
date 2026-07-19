"""Presage dashboard API.

Run from the dashboard/ directory:
    uvicorn backend.app.main:app --port 8000

Serves the JSON API under /api and, when frontend/dist exists, the built
React app at /.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.core.state import ModelStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    store = ModelStore(settings.model_path, settings.data_dir)
    store.load()
    app.state.store = store
    yield


app = FastAPI(title="Presage API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

if settings.frontend_dist.is_dir():
    app.mount("/assets",
              StaticFiles(directory=settings.frontend_dist / "assets"),
              name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str) -> FileResponse:
        """SPA fallback: serve real files, else index.html (client routing)."""
        candidate = settings.frontend_dist / full_path
        if full_path and ".." not in full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(settings.frontend_dist / "index.html")
