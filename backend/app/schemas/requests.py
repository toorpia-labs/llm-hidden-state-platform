from pydantic import BaseModel, Field


class ModelLoadRequest(BaseModel):
    model_id: str


class ExtractionRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000)
    n_trials: int = Field(default=10, ge=1, le=100)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_new_tokens: int = Field(default=100, ge=10, le=500)
    layer: int = Field(default=-1, ge=-100, le=100)
    n_segments: int = Field(default=10, ge=5, le=50)
    overlap: float = Field(default=0.5, ge=0.0, le=0.9)
    window_func: str = Field(default="hann", pattern="^(rect|hann|hamming)$")


class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    is_loaded: bool
    note: str | None = None


class ModelsResponse(BaseModel):
    models: list[ModelInfo]
    current_model: str | None


class ModelLoadResponse(BaseModel):
    status: str
    model_id: str
    message: str


class JobStartResponse(BaseModel):
    job_id: str
    status: str
    model_id: str
    message: str


class JobProgress(BaseModel):
    completed: int
    total: int


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: JobProgress | None = None
    model_id: str | None = None
    metadata: dict | None = None
    files: dict | None = None
    generations: list[str] | None = None
    error: str | None = None
