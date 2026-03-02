import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import MODELS_CONFIG_PATH
from .models.llm_worker import LLMWorker
from .services.job_manager import JobManager
from .routes import models as models_route
from .routes import extract as extract_route
from .routes import results as results_route

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="LLM Hidden State Extraction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons
worker = LLMWorker(models_config_path=MODELS_CONFIG_PATH)
job_manager = JobManager()

# Register routers
app.include_router(models_route.router)
app.include_router(extract_route.router)
app.include_router(results_route.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "current_model": worker.current_model_id,
        "is_loading": worker.is_loading,
    }
