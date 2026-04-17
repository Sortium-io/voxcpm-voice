#!/usr/bin/env python3
"""Generate a voice WAV (or N takes of one) using VoxCPM2 voice design.

Composes text as `(voice_fantasy)(emotion)(chinese_hype)sentences!` — stacked
parenthesized directives that VoxCPM reads as voice conditioning, followed by
the sentences to speak. One generate() call per take; each take is an
independent render (stochastically varied).

Writes WAVs to ~/voxcpm-voice/outputs/ (override with --output-dir).
Single take:  <voice_name>.wav
Multi-take:   <voice_name>_t1.wav, <voice_name>_t2.wav, ...
"""
from __future__ import annotations
import argparse
import os
import re
import sys
import time
from pathlib import Path

os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

DEFAULT_LINES = [
    "The birch canoe slid on the smooth planks.",
    "Glue the sheet to the dark blue background.",
    "It's easy to tell the depth of a well.",
]
CHINESE_HYPE_DIRECTIVE = "请用极度激动和兴奋的语气大声喊这些句子"
DEFAULT_OUTPUT_DIR = Path.home() / "voxcpm-voice" / "outputs"


def slugify(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_")
    return cleaned or "voice"


def build_text(
    lines: list[str],
    voice_fantasy: str = "",
    emotion: str = "",
    chinese_hype: bool = True,
) -> str:
    """Stack directives then join sentences with exclamation emphasis."""
    directives: list[str] = []
    if voice_fantasy.strip():
        directives.append(f"({voice_fantasy.strip()})")
    if emotion.strip():
        directives.append(f"({emotion.strip()})")
    if chinese_hype:
        directives.append(f"({CHINESE_HYPE_DIRECTIVE})")

    # Normalize terminal punctuation → exclamation for each sentence.
    emphasized = []
    for line in lines:
        stripped = line.strip().rstrip(".!?")
        emphasized.append(stripped + "!" if stripped else "")
    body = " ".join(s for s in emphasized if s)
    return "".join(directives) + body


def find_internal_gaps(audio, sr: int, threshold: float, min_gap_ms: int):
    """Return (start, end) sample indices for silence runs strictly inside the clip."""
    import numpy as np

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


def pad_silences(audio, sr: int, threshold=0.01, min_gap_ms=200, target_ms=600):
    import numpy as np

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


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Generate a voice WAV using VoxCPM2 voice design.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--voice-name", required=True,
                    help="Slug for output filename, e.g. 'Drill_Sergeant'")
    ap.add_argument("--voice-fantasy", default="",
                    help="Concrete voice description (age/gender/timbre/accent). Becomes 1st () directive.")
    ap.add_argument("--emotion", default="",
                    help="Style/energy directive. Becomes 2nd () directive.")
    ap.add_argument("--no-chinese-hype", action="store_true",
                    help="Skip the Chinese emotion directive (on by default — VoxCPM2 responds strongly to it).")
    ap.add_argument("--takes", type=int, default=1,
                    help="Number of independent renders (default 1). Each take is stochastically different.")
    ap.add_argument("--lines", nargs="+", default=None,
                    help="Override the three test sentences (default: Harvard sentences).")
    ap.add_argument("--cfg-value", type=float, default=2.0,
                    help="VoxCPM classifier-free guidance (default 2.0 — README-evaluated).")
    ap.add_argument("--inference-timesteps", type=int, default=10,
                    help="Diffusion steps (default 10 — README-evaluated).")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                    help=f"Output directory (default {DEFAULT_OUTPUT_DIR}).")
    ap.add_argument("--skip-padding", action="store_true",
                    help="Skip the inter-sentence silence padding post-step.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the composed text and target paths, do not invoke the model.")
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    lines = args.lines if args.lines else DEFAULT_LINES
    text = build_text(
        lines=lines,
        voice_fantasy=args.voice_fantasy,
        emotion=args.emotion,
        chinese_hype=not args.no_chinese_hype,
    )

    slug = slugify(args.voice_name)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.takes == 1:
        target_paths = [args.output_dir / f"{slug}.wav"]
    else:
        target_paths = [args.output_dir / f"{slug}_t{i + 1}.wav" for i in range(args.takes)]

    print(f"[voxcpm-voice] composed text:\n  {text}\n", flush=True)
    print(f"[voxcpm-voice] takes: {args.takes}  cfg: {args.cfg_value}  "
          f"timesteps: {args.inference_timesteps}", flush=True)
    print(f"[voxcpm-voice] output paths:", flush=True)
    for p in target_paths:
        print(f"  {p}", flush=True)

    if args.dry_run:
        print("\n[voxcpm-voice] --dry-run set; not generating.")
        return

    # Import heavy deps only when actually generating.
    from voxcpm import VoxCPM
    import soundfile as sf
    import numpy as np

    print("\n[voxcpm-voice] loading VoxCPM2 (first run downloads ~2GB model weights)...", flush=True)
    t0 = time.time()
    model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
    sr = model.tts_model.sample_rate
    print(f"[voxcpm-voice] model ready in {time.time() - t0:.1f}s  sr={sr}", flush=True)

    for i, out_path in enumerate(target_paths, 1):
        t_start = time.time()
        wav = model.generate(
            text=text,
            cfg_value=args.cfg_value,
            inference_timesteps=args.inference_timesteps,
        )
        wav_np = np.asarray(wav, dtype=np.float32)
        extended = 0
        if not args.skip_padding:
            wav_np, extended = pad_silences(wav_np, sr)

        sf.write(str(out_path), wav_np, sr)
        dur_audio = len(wav_np) / sr
        dur_wall = time.time() - t_start
        note = f"(padded {extended} gap{'s' if extended != 1 else ''})" if not args.skip_padding else ""
        print(f"[voxcpm-voice] take {i}/{args.takes}  {dur_wall:5.1f}s wall  "
              f"{dur_audio:5.1f}s audio  -> {out_path.name}  {note}", flush=True)

    print(f"\n[voxcpm-voice] done. {args.takes} file(s) in {args.output_dir}")


if __name__ == "__main__":
    main()
