from fastapi import APIRouter, Depends

from backend.app.api.deps import get_store, validate_horizon
from backend.app.core.state import ModelStore
from backend.app.schemas.narrative import NarrativeRequest, NarrativeResponse
from backend.app.services import narrative_service

router = APIRouter()


@router.post("/narrative", response_model=NarrativeResponse)
def create_narrative(body: NarrativeRequest,
                     store: ModelStore = Depends(get_store)) -> NarrativeResponse:
    """Sync def on purpose: FastAPI runs it in the threadpool, so the
    (potentially slow) provider call never blocks the event loop."""
    validate_horizon(store, body.horizon)
    return narrative_service.make_narrative(store, body.horizon, body.budgets)
