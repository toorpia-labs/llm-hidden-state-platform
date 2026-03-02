import json
import logging
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import DATA_DIR
from ..services.extraction import compute_segment_metadata, validate_output

logger = logging.getLogger(__name__)


class JobManager:
    def __init__(self):
        self.jobs: dict[str, dict] = {}

    def create_job(self, model_id: str, params: dict) -> str:
        """新しいジョブを作成し、job_idを返す"""
        job_id = str(uuid.uuid4())
        job_dir = DATA_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        job = {
            "job_id": job_id,
            "status": "queued",
            "model_id": model_id,
            "params": params,
            "progress": {"completed": 0, "total": params["n_trials"]},
            "job_dir": str(job_dir),
        }
        self.jobs[job_id] = job
        self._save_status(job_id)
        return job_id

    def update_progress(self, job_id: str, completed: int, total: int):
        """進捗を更新"""
        if job_id in self.jobs:
            self.jobs[job_id]["progress"] = {"completed": completed, "total": total}
            self.jobs[job_id]["status"] = "running"
            self._save_status(job_id)

    def complete_job(
        self,
        job_id: str,
        segments_list: list[np.ndarray],
        positions_list: list[list[float]],
        generations: list[str],
        trial_metadata: list[dict],
        params: dict,
    ):
        """ジョブを完了し、ファイルを保存"""
        job_dir = Path(self.jobs[job_id]["job_dir"])

        # segments.csv を生成
        rows = []
        for trial_idx, (segments, positions) in enumerate(zip(segments_list, positions_list)):
            if not validate_output(segments, params["n_segments"]):
                logger.warning(f"Trial {trial_idx}: output validation failed")

            for seg_idx in range(segments.shape[0]):
                row = {
                    "trial_id": trial_idx,
                    "segment_index": seg_idx,
                    "segment_position": round(positions[seg_idx], 6),
                }
                for dim_idx in range(segments.shape[1]):
                    row[f"dim_{dim_idx}"] = float(segments[seg_idx, dim_idx])
                rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(job_dir / "segments.csv", index=False)

        # metadata.json
        all_meta = []
        for trial_idx, (segs, meta) in enumerate(zip(segments_list, trial_metadata)):
            trial_meta = compute_segment_metadata(
                hidden_states=np.zeros((meta["num_generated_tokens"], meta["hidden_dim"])),
                segments=segs,
                n_segments=params["n_segments"],
                overlap=params["overlap"],
                window_func=params["window_func"],
                layer_idx=params["layer"],
            )
            trial_meta["trial_id"] = trial_idx
            trial_meta.update(meta)
            all_meta.append(trial_meta)

        metadata = {
            "model_id": self.jobs[job_id]["model_id"],
            "prompt": params["prompt"],
            "n_trials": params["n_trials"],
            "temperature": params["temperature"],
            "max_new_tokens": params["max_new_tokens"],
            "layer": params["layer"],
            "n_segments": params["n_segments"],
            "overlap": params["overlap"],
            "window_func": params["window_func"],
            "trials": all_meta,
        }
        with open(job_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # generations.txt
        with open(job_dir / "generations.txt", "w") as f:
            for i, text in enumerate(generations):
                f.write(f"=== Trial {i} ===\n")
                f.write(text)
                f.write("\n\n")

        self.jobs[job_id]["status"] = "completed"
        self.jobs[job_id]["metadata"] = metadata
        self.jobs[job_id]["generations"] = generations
        self._save_status(job_id)

    def fail_job(self, job_id: str, error: str):
        """ジョブを失敗として記録"""
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["error"] = error
            self._save_status(job_id)

    def get_job(self, job_id: str) -> dict | None:
        return self.jobs.get(job_id)

    def get_job_dir(self, job_id: str) -> Path | None:
        job = self.jobs.get(job_id)
        if job:
            return Path(job["job_dir"])
        return None

    def _save_status(self, job_id: str):
        """status.jsonをジョブディレクトリに保存"""
        job = self.jobs[job_id]
        job_dir = Path(job["job_dir"])
        status = {
            "job_id": job["job_id"],
            "status": job["status"],
            "model_id": job["model_id"],
            "progress": job.get("progress"),
        }
        with open(job_dir / "status.json", "w") as f:
            json.dump(status, f, indent=2)
