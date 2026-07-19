from fastapi import APIRouter, Depends

from backend.app.api.deps import get_store, validate_horizon
from backend.app.core.state import ModelStore
from backend.app.schemas.common import ScenarioRequest
from backend.app.schemas.simulator import SimulatorResponse
from backend.app.services import simulator_service

router = APIRouter()


@router.post("/response-curves", response_model=SimulatorResponse)
def create_response_curves(body: ScenarioRequest,
                           store: ModelStore = Depends(get_store)) -> SimulatorResponse:
    validate_horizon(store, body.horizon)
    return simulator_service.get_curves(store, body.horizon, body.budgets)
