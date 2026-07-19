from fastapi import APIRouter, Depends

from backend.app.api.deps import get_store
from backend.app.core.state import ModelStore
from backend.app.schemas.anomalies import AnomaliesResponse
from backend.app.services import anomaly_service

router = APIRouter()


@router.get("/anomalies", response_model=AnomaliesResponse)
def read_anomalies(store: ModelStore = Depends(get_store)) -> AnomaliesResponse:
    return anomaly_service.get_anomalies(store)
