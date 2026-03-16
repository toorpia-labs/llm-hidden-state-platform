"""
backend/app/utils/device.py

Central device detection for CUDA (Linux production) and
MPS / CPU (macOS development) backends.

  - CUDA available  → cuda  (production, RTX 3050)
  - MPS available   → mps   (macOS M-series dev)
  - otherwise       → cpu

All other modules should import from here instead of
calling torch.cuda.* or torch.backends.mps.* directly.
"""

import logging
import platform

import torch

logger = logging.getLogger(__name__)


def _detect_backend() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if platform.system() == "Darwin" and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


BACKEND: str = _detect_backend()
IS_CUDA: bool = BACKEND == "cuda"
IS_MPS: bool = BACKEND == "mps"
IS_CPU: bool = BACKEND == "cpu"

logger.info(f"[device] Active backend: {BACKEND}")


def get_device() -> torch.device:
    return torch.device(BACKEND)


def empty_cache() -> None:
    """Release cached memory for the active backend."""
    if IS_CUDA:
        torch.cuda.empty_cache()
    elif IS_MPS:
        if hasattr(torch.mps, "empty_cache"):
            torch.mps.empty_cache()


def get_device_map() -> str | None:
    """
    Return device_map for from_pretrained().
    CUDA → "auto"; MPS/CPU → None (model must be moved manually with .to()).
    """
    if IS_CUDA:
        return "auto"
    return None


def get_dtype_for_model(requested_dtype_str: str) -> torch.dtype:
    """
    Resolve torch dtype, applying MPS-safe override.
    MPS + float16 → bfloat16 (float16 is unreliable on MPS for some ops).
    """
    requested = getattr(torch, requested_dtype_str, torch.float16)
    if IS_MPS and requested == torch.float16:
        logger.info("[device] MPS backend: overriding float16 → bfloat16")
        return torch.bfloat16
    return requested


def quantization_supported() -> bool:
    """4-bit quantization (bitsandbytes) is CUDA-only."""
    return IS_CUDA
