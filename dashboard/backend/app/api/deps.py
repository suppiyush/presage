"""Shared FastAPI dependencies."""

from fastapi import HTTPException, Request

from backend.app.core.state import ModelStore


def get_store(request: Request) -> ModelStore:
    return request.app.state.store


def validate_horizon(store: ModelStore, horizon: int) -> int:
    if horizon not in store.horizons:
        raise HTTPException(status_code=422,
                            detail=f"horizon must be one of {store.horizons}")
    return horizon
