from fastapi import APIRouter, HTTPException

from ..schemas.requests import ModelLoadRequest, ModelLoadResponse, ModelsResponse

router = APIRouter()


def get_worker():
    from ..main import worker
    return worker


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    w = get_worker()
    models = w.list_available_models()
    return ModelsResponse(
        models=models,
        current_model=w.current_model_id,
    )


@router.post("/models/load", response_model=ModelLoadResponse)
async def load_model(request: ModelLoadRequest):
    w = get_worker()
    if w.is_loading:
        raise HTTPException(status_code=409, detail="Another model is currently being loaded")
    try:
        result = await w.load_model(request.model_id)
        return ModelLoadResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
