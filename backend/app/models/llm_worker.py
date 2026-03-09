import asyncio
import gc
import logging
import time
from pathlib import Path

import numpy as np
import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from ..services.extraction import (
    create_overlapping_segments,
    extract_hidden_states_from_generation,
)

logger = logging.getLogger(__name__)


class LLMWorker:
    def __init__(self, models_config_path: str | Path = "models.yaml"):
        self.model = None
        self.tokenizer = None
        self.current_model_id: str | None = None
        self.lock = asyncio.Lock()
        self.registry = self._load_registry(models_config_path)
        self._loading = False

    def _load_registry(self, path: str | Path) -> dict:
        """models.yaml を読み込み、id -> 設定 の辞書を返す"""
        path = Path(path)
        if not path.exists():
            logger.warning(f"Models config not found: {path}")
            return {}
        with open(path) as f:
            data = yaml.safe_load(f)
        return {m["id"]: m for m in data.get("models", [])}

    def list_available_models(self) -> list[dict]:
        """利用可能なモデル一覧を返す（UI表示用）"""
        return [
            {
                "id": m["id"],
                "name": m["name"],
                "description": m["description"],
                "is_loaded": m["id"] == self.current_model_id,
            }
            for m in self.registry.values()
        ]

    @property
    def is_loading(self) -> bool:
        return self._loading

    async def load_model(self, model_id: str) -> dict:
        """
        指定モデルをロード。既に別モデルがロード済みなら先にアンロードする。
        同一モデルが既にロード済みなら何もしない。
        """
        async with self.lock:
            if model_id == self.current_model_id:
                return {"status": "already_loaded", "model_id": model_id, "message": "Model already loaded"}

            if model_id not in self.registry:
                raise ValueError(f"Unknown model: {model_id}")

            self._loading = True
            try:
                start_time = time.time()

                # 現モデルをアンロード（VRAM解放）
                if self.model is not None:
                    del self.model
                    del self.tokenizer
                    self.model = None
                    self.tokenizer = None
                    self.current_model_id = None
                    torch.cuda.empty_cache()
                    gc.collect()

                # 新モデルをロード
                config = self.registry[model_id]
                logger.info(f"Loading model: {config['hf_repo']}")

                self.tokenizer = await asyncio.to_thread(
                    AutoTokenizer.from_pretrained,
                    config["hf_repo"],
                    trust_remote_code=True,
                )

                load_kwargs = {
                    "dtype": getattr(torch, config.get("torch_dtype", "float16")),
                    "device_map": "auto",
                    "trust_remote_code": True,
                }
                if config.get("quantize"):
                    load_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)

                self.model = await asyncio.to_thread(
                    AutoModelForCausalLM.from_pretrained,
                    config["hf_repo"],
                    **load_kwargs,
                )
                self.model.eval()
                self.current_model_id = model_id

                elapsed = time.time() - start_time
                logger.info(f"Model {model_id} loaded in {elapsed:.1f}s")
                return {
                    "status": "loaded",
                    "model_id": model_id,
                    "message": f"Model loaded successfully (took {elapsed:.1f}s)",
                }
            finally:
                self._loading = False

    def _generate_single(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        temperature: float,
        max_new_tokens: int,
    ):
        """1回の生成を実行し、outputsを返す"""
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                output_hidden_states=True,
                return_dict_in_generate=True,
            )
        return outputs

    async def generate_with_hidden_states(
        self,
        prompt: str,
        n_trials: int,
        temperature: float = 0.7,
        max_new_tokens: int = 100,
        layer: int = -1,
        n_segments: int = 10,
        overlap: float = 0.5,
        window_func: str = "hann",
        progress_callback=None,
    ) -> dict:
        """排他制御付きで推論実行。モデル未ロード時はエラー。"""
        if self.model is None:
            raise RuntimeError("No model loaded. Call POST /models/load first.")

        async with self.lock:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            input_ids = inputs["input_ids"].to(self.model.device)
            attention_mask = inputs["attention_mask"].to(self.model.device)
            input_length = input_ids.shape[1]

            all_segments = []
            all_positions = []
            all_generations = []
            all_metadata = []
            all_hidden_states = []

            for trial in range(n_trials):
                outputs = await asyncio.to_thread(
                    self._generate_single,
                    input_ids,
                    attention_mask,
                    temperature,
                    max_new_tokens,
                )

                # 生成テキスト
                generated_ids = outputs.sequences[0][input_length:]
                generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
                all_generations.append(generated_text)

                # hidden state抽出
                hidden_states = extract_hidden_states_from_generation(
                    outputs, input_length, layer_idx=layer
                )

                # セグメンテーション
                segments, positions = create_overlapping_segments(
                    hidden_states, n_segments, overlap, window_func
                )

                all_segments.append(segments)
                all_positions.append(positions)
                all_hidden_states.append(hidden_states)

                # メタデータ
                all_metadata.append({
                    "num_generated_tokens": int(generated_ids.shape[0]),
                    "hidden_dim": int(hidden_states.shape[1]),
                    "actual_segments": int(segments.shape[0]),
                })

                if progress_callback:
                    await progress_callback(trial + 1, n_trials)

            return {
                "segments": all_segments,
                "positions": all_positions,
                "generations": all_generations,
                "trial_metadata": all_metadata,
                "hidden_states": all_hidden_states,
                "input_length": input_length,
            }
