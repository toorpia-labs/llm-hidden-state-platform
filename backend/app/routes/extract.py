import asyncio
import logging

from fastapi import APIRouter, HTTPException

from ..schemas.requests import ExtractionRequest, JobStartResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def get_worker():
    from ..main import worker
    return worker


def get_job_manager():
    from ..main import job_manager
    return job_manager


async def _run_extraction(job_id: str, request: ExtractionRequest):
    """バックグラウンドで抽出を実行"""
    w = get_worker()
    jm = get_job_manager()

    try:
        jm.update_progress(job_id, 0, request.n_trials)

        async def progress_callback(completed: int, total: int):
            jm.update_progress(job_id, completed, total)

        result = await w.generate_with_hidden_states(
            prompt=request.prompt,
            n_trials=request.n_trials,
            temperature=request.temperature,
            max_new_tokens=request.max_new_tokens,
            layer=request.layer,
            n_segments=request.n_segments,
            overlap=request.overlap,
            window_func=request.window_func,
            progress_callback=progress_callback,
        )

        jm.complete_job(
            job_id=job_id,
            segments_list=result["segments"],
            positions_list=result["positions"],
            generations=result["generations"],
            trial_metadata=result["trial_metadata"],
            params={
                "prompt": request.prompt,
                "n_trials": request.n_trials,
                "temperature": request.temperature,
                "max_new_tokens": request.max_new_tokens,
                "layer": request.layer,
                "n_segments": request.n_segments,
                "overlap": request.overlap,
                "window_func": request.window_func,
            },
        )
    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        jm.fail_job(job_id, str(e))


@router.post("/extract", response_model=JobStartResponse)
async def start_extraction(request: ExtractionRequest):
    w = get_worker()
    if w.model is None:
        raise HTTPException(
            status_code=400,
            detail="No model loaded. Use POST /models/load first.",
        )

    jm = get_job_manager()
    job_id = jm.create_job(
        model_id=w.current_model_id,
        params=request.model_dump(),
    )

    asyncio.create_task(_run_extraction(job_id, request))

    return JobStartResponse(
        job_id=job_id,
        status="running",
        model_id=w.current_model_id,
        message=f"Extraction started with {request.n_trials} trials using {w.current_model_id}",
    )
