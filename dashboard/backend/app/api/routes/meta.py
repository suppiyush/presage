from fastapi import APIRouter, Depends

from backend.app.api.deps import get_store
from backend.app.core.state import ModelStore
from backend.app.schemas.meta import MetaResponse
from backend.app.services import meta_service

router = APIRouter()


@router.get("/meta", response_model=MetaResponse)
def read_meta(store: ModelStore = Depends(get_store)) -> MetaResponse:
    return meta_service.get_meta(store)
