from fastapi import APIRouter

from backend.app.api.routes import (simulator)
from backend.app.api.routes import allocation, anomalies, forecast, meta, narrative

api_router = APIRouter(prefix="/api")
api_router.include_router(meta.router, tags=["meta"])
api_router.include_router(forecast.router, tags=["forecast"])
api_router.include_router(simulator.router, tags=["simulator"])
api_router.include_router(allocation.router, tags=["allocation"])
api_router.include_router(anomalies.router, tags=["anomalies"])
api_router.include_router(narrative.router, tags=["narrative"])
