from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse

from backend.app.api.deps import get_store, validate_horizon
from backend.app.core.state import ModelStore
from backend.app.schemas.forecast import ForecastRequest, ForecastResponse
from backend.app.services import forecast_service

router = APIRouter()


@router.post("/forecast", response_model=ForecastResponse)
def create_forecast(body: ForecastRequest,
                    store: ModelStore = Depends(get_store)) -> ForecastResponse:
    validate_horizon(store, body.horizon)
    return forecast_service.get_forecast(store, body.horizon, body.budgets)


@router.get("/forecast/export", response_class=PlainTextResponse)
def export_forecast(request: Request,
                    horizon: int = Query(30),
                    store: ModelStore = Depends(get_store)) -> PlainTextResponse:
    """CSV download. Channel budgets are passed as query params, e.g.
    /api/forecast/export?horizon=30&google=45714&meta=6870."""
    validate_horizon(store, horizon)
    budgets = {}
    for ch in store.channels:
        raw = request.query_params.get(ch)
        if raw is not None:
            try:
                budgets[ch] = float(raw)
            except ValueError:
                pass
    csv_text = forecast_service.forecast_csv(store, horizon, budgets)
    return PlainTextResponse(
        csv_text, media_type="text/csv",
        headers={"Content-Disposition":
                 f'attachment; filename="forecast_{horizon}d.csv"'})
