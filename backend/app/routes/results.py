from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..schemas.requests import JobStatusResponse, JobProgress

router = APIRouter()


def get_job_manager():
    from ..main import job_manager
    return job_manager


@router.get("/results/{job_id}", response_model=JobStatusResponse)
async def get_results(job_id: str):
    jm = get_job_manager()
    job = jm.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    response = {
        "job_id": job["job_id"],
        "status": job["status"],
    }

    if job.get("progress"):
        response["progress"] = JobProgress(**job["progress"])

    if job["status"] == "completed":
        response["model_id"] = job["model_id"]
        response["metadata"] = job.get("metadata")
        response["files"] = {
            "segments_csv": f"/results/{job_id}/download/segments.csv",
            "metadata_json": f"/results/{job_id}/download/metadata.json",
            "generations_txt": f"/results/{job_id}/download/generations.txt",
        }
        response["generations"] = job.get("generations")

    if job["status"] == "failed":
        response["model_id"] = job["model_id"]

    return JobStatusResponse(**response)


ALLOWED_FILES = {"segments.csv", "metadata.json", "generations.txt"}


@router.get("/results/{job_id}/download/{filename}")
async def download_file(job_id: str, filename: str):
    if filename not in ALLOWED_FILES:
        raise HTTPException(status_code=400, detail=f"Invalid filename. Allowed: {ALLOWED_FILES}")

    jm = get_job_manager()
    job_dir = jm.get_job_dir(job_id)
    if not job_dir:
        raise HTTPException(status_code=404, detail="Job not found")

    file_path = job_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
    )
