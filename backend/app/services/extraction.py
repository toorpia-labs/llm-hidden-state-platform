import numpy as np
from scipy.signal import get_window


def extract_hidden_states_from_generation(outputs, input_length: int, layer_idx: int = -1) -> np.ndarray:
    """
    outputs.hidden_states はタプルのタプル:
        hidden_states[token_idx][layer_idx] -> (batch, seq_len, hidden_dim)
    各生成ステップの最後のポジション（新規トークン）のhidden stateを取得
    """
    hidden_states_list = []
    for token_idx in range(len(outputs.hidden_states)):
        step_hidden = outputs.hidden_states[token_idx]
        layer_hidden = step_hidden[layer_idx]
        token_hidden = layer_hidden[0, -1, :].cpu().numpy()
        hidden_states_list.append(token_hidden)
    return np.stack(hidden_states_list, axis=0)


def create_overlapping_segments(
    hidden_states: np.ndarray,
    n_segments: int,
    overlap: float = 0.5,
    window_func: str = "hann",
) -> tuple[np.ndarray, list[float]]:
    """
    STFT風オーバーラップ窓によるセグメンテーション
    hidden_states: (num_tokens, hidden_dim) -> segments: (n_segments, hidden_dim)

    Returns:
        segments: (n_segments, hidden_dim)
        positions: list of normalized positions (0.0 to 1.0)
    """
    num_tokens, hidden_dim = hidden_states.shape

    if num_tokens < n_segments:
        n_segments = num_tokens

    hop = max(1, (num_tokens - 1) / max(1, n_segments - 1))
    window_size = max(1, int(hop / (1.0 - overlap))) if overlap < 1.0 else num_tokens

    if window_func == "rect":
        window = np.ones(window_size)
    else:
        window = get_window(window_func, window_size)

    segments = []
    positions = []

    for i in range(n_segments):
        center = int(i * hop)
        start = max(0, center - window_size // 2)
        end = min(num_tokens, start + window_size)
        actual_size = end - start

        w = window[:actual_size] if actual_size < window_size else window
        w = w / (w.sum() + 1e-10)

        segment = hidden_states[start:end]
        weighted = segment * w[:, np.newaxis]
        segments.append(weighted.sum(axis=0))
        positions.append(center / max(1, num_tokens - 1))

    return np.stack(segments, axis=0), positions


def compute_segment_metadata(
    hidden_states: np.ndarray,
    segments: np.ndarray,
    n_segments: int,
    overlap: float,
    window_func: str,
    layer_idx: int,
) -> dict:
    """メタデータ計算"""
    return {
        "num_tokens": int(hidden_states.shape[0]),
        "hidden_dim": int(hidden_states.shape[1]),
        "n_segments": int(segments.shape[0]),
        "overlap": overlap,
        "window_func": window_func,
        "layer": layer_idx,
        "hidden_state_stats": {
            "mean": float(np.mean(hidden_states)),
            "std": float(np.std(hidden_states)),
            "min": float(np.min(hidden_states)),
            "max": float(np.max(hidden_states)),
        },
    }


def validate_output(segments: np.ndarray, n_segments: int) -> bool:
    """出力検証"""
    if segments.ndim != 2:
        return False
    if segments.shape[0] < 1:
        return False
    if np.any(np.isnan(segments)):
        return False
    if np.any(np.isinf(segments)):
        return False
    return True
