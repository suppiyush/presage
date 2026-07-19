from fastapi import APIRouter, Depends

from backend.app.api.deps import get_store, validate_horizon
from backend.app.core.state import ModelStore
from backend.app.schemas.allocation import AllocationResponse
from backend.app.schemas.common import ScenarioRequest
from backend.app.services import allocation_service

router = APIRouter()


@router.post("/allocation", response_model=AllocationResponse)
def create_allocation(body: ScenarioRequest,
                      store: ModelStore = Depends(get_store)) -> AllocationResponse:
    validate_horizon(store, body.horizon)
    return allocation_service.get_allocation(store, body.horizon, body.budgets)
