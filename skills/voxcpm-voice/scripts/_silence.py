"""Silence padding — enforces a minimum inter-sentence gap so takes don't smush.

Detects internal silence runs (amplitude below threshold for at least min_gap_ms)
and extends any gap shorter than target_ms up to target_ms. Leading and trailing
silence is preserved as-is — we only pad silences between spoken segments.
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
        out.append(audio[cursor:end])
        if run_len < target_len:
            pad = np.zeros(target_len - run_len, dtype=audio.dtype)
            out.append(pad)
            extended += 1
        cursor = end
    out.append(audio[cursor:])
    return np.concatenate(out), extended
