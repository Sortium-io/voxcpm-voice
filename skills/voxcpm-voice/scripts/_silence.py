"""Silence padding — enforces a minimum inter-sentence gap so takes don't smush.

Detects internal silence runs (amplitude below threshold for at least min_gap_ms)
and extends any gap shorter than target_ms up to target_ms. Leading and trailing
silence is preserved as-is — we only extend silences between spoken segments.

Extension strategy: *tile* the detected gap's own samples until we reach
target_ms. This preserves whatever noise-floor texture VoxCPM produced in that
gap, so there's no step discontinuity at the boundary between the existing gap
and the padding. That discontinuity (noise-floor → true zero → noise-floor) is
what caused audible clicks on CUDA bf16 output, where the noise floor sits
~0.005 and the jump to exact 0.0 is in-band. Tiling makes the extension
continuous with the surrounding room tone.
"""
from __future__ import annotations

import numpy as np


def find_internal_gaps(audio: np.ndarray, sr: int, threshold: float, min_gap_ms: int):
    silent = np.abs(audio) < threshold
    if not silent.any() or silent.all():
        return []

    voiced = np.where(~silent)[0]
    first, last = int(voiced[0]), int(voiced[-1])
    interior = silent[first : last + 1]
    min_len = int(sr * min_gap_ms / 1000)

    gaps, i, n = [], 0, len(interior)
    while i < n:
        if interior[i]:
            j = i
            while j < n and interior[j]:
                j += 1
            if (j - i) >= min_len:
                gaps.append((first + i, first + j))
            i = j
        else:
            i += 1
    return gaps


def _extend_gap_by_tiling(gap_samples: np.ndarray, target_len: int) -> np.ndarray:
    """Tile gap_samples (reversing every other rep) until the result is target_len long.

    Reversing every other rep prevents a zero-crossing discontinuity at tile
    boundaries — the end of rep N matches the start of rep N+1 sample-for-sample.
    """
    if gap_samples.size == 0:
        return np.zeros(target_len, dtype=gap_samples.dtype)
    chunks = []
    covered = 0
    flip = False
    while covered < target_len:
        chunk = gap_samples[::-1] if flip else gap_samples
        chunks.append(chunk)
        covered += chunk.size
        flip = not flip
    return np.concatenate(chunks)[:target_len].astype(gap_samples.dtype)


def pad_silences(audio: np.ndarray, sr: int, threshold=0.01, min_gap_ms=200, target_ms=600):
    """Return (padded_audio, num_gaps_extended)."""
    gaps = find_internal_gaps(audio, sr, threshold, min_gap_ms)
    if not gaps:
        return audio, 0

    target_len = int(sr * target_ms / 1000)
    extended = 0
    out, cursor = [], 0
    for start, end in gaps:
        run_len = end - start
        out.append(audio[cursor:start])  # audio leading up to the gap
        if run_len < target_len:
            out.append(_extend_gap_by_tiling(audio[start:end], target_len))
            extended += 1
        else:
            out.append(audio[start:end])
        cursor = end
    out.append(audio[cursor:])
    return np.concatenate(out), extended
