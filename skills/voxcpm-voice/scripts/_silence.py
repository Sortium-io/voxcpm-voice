"""Silence padding — enforces a minimum inter-sentence gap so takes don't smush.

Detects internal silence runs (amplitude below threshold for at least min_gap_ms)
and extends any gap shorter than target_ms up to target_ms. Leading and trailing
silence is preserved as-is — we only extend silences between spoken segments.

Extension strategy: keep the original gap samples verbatim, then append
Gaussian noise at the SAME RMS as the detected gap to reach target_ms, with a
short crossfade at the join so there's no amplitude discontinuity. This avoids
two different kinds of click artifact:

  1. Filling with literal zeros produces a step from the model's noise floor
     (~0.005 on CUDA bf16) down to exact 0.0 and back, which is audibly clicky.
  2. Tiling the gap samples (previous approach) preserves one-shot transients
     that VoxCPM can emit at sentence boundaries — a single tick becomes 2-3
     ticks, sounding like rhythmic clicking.

Matched-RMS Gaussian noise is continuous, non-repeating, and phase-neutral —
it's just the gap's own room tone continuing naturally.
"""
from __future__ import annotations

import numpy as np

_RNG = np.random.default_rng(42)  # deterministic across runs for reproducibility


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


def _extend_gap_with_noise(gap_samples: np.ndarray, target_len: int) -> np.ndarray:
    """Fill to target_len with matched-RMS Gaussian noise, crossfaded at the join."""
    if gap_samples.size >= target_len:
        return gap_samples[:target_len]
    if gap_samples.size == 0:
        return np.zeros(target_len, dtype=np.float32).astype(gap_samples.dtype)

    gap_f = gap_samples.astype(np.float32)
    rms = float(np.sqrt(np.mean(gap_f ** 2)))
    # Clamp to a perceptually silent floor if the gap really is pure zeros —
    # keeps the noise *just* loud enough to avoid step discontinuities at the
    # join but quiet enough to be imperceptible.
    if rms < 1e-6:
        rms = 1e-5

    extra = target_len - gap_samples.size
    noise = (_RNG.standard_normal(extra) * rms).astype(np.float32)

    out = np.empty(target_len, dtype=np.float32)
    out[:gap_samples.size] = gap_f
    out[gap_samples.size:] = noise

    # Crossfade the join (up to ~2.5 ms) so there's no amplitude step at the
    # transition between original gap samples and appended noise.
    fade_len = min(128, gap_samples.size, extra)
    if fade_len > 0:
        w = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
        i = gap_samples.size - fade_len
        out[i:i + fade_len] = gap_f[-fade_len:] * (1.0 - w) + noise[:fade_len] * w

    return out.astype(gap_samples.dtype)


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
            out.append(_extend_gap_with_noise(audio[start:end], target_len))
            extended += 1
        else:
            out.append(audio[start:end])
        cursor = end
    out.append(audio[cursor:])
    return np.concatenate(out), extended
