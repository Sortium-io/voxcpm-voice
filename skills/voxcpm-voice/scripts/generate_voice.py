#!/usr/bin/env python3
"""Design a new voice using VoxCPM2 voice design (text-only TTS).

Writes each take to ~/voxcpm-voice/voices/<name>/samples/t<N>.wav and writes
voice.json with the full prompt + the sentences that were spoken (so speak.py
can use Ultimate Cloning later).

Re-running with the same --voice-name overwrites samples/ but leaves
reference.wav and lines/ untouched — so you can keep iterating on the design
without losing a good reference you already saved.

Use --save-take N to promote a sample to reference.wav in the same run, or run
save_take.py afterward once you've listened.
"""
from __future__ import annotations
import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _console  # noqa: F401, E402  — reconfigures stdout to UTF-8 on Windows
from _library import (  # noqa: E402
    DEFAULT_LINES,
    VoiceMeta,
    samples_dir,
    slugify,
    promote_take,
)
from _silence import pad_silences  # noqa: E402

os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

CHINESE_HYPE_DIRECTIVE = "请用极度激动和兴奋的语气大声喊这些句子"


def build_text(
    lines: list[str],
    voice_fantasy: str = "",
    emotion: str = "",
    chinese_hype: bool = True,
) -> str:
    directives: list[str] = []
    if voice_fantasy.strip():
        directives.append(f"({voice_fantasy.strip()})")
    if emotion.strip():
        directives.append(f"({emotion.strip()})")
    if chinese_hype:
        directives.append(f"({CHINESE_HYPE_DIRECTIVE})")
    emphasized = []
    for line in lines:
        stripped = line.strip().rstrip(".!?")
        if stripped:
            emphasized.append(stripped + "!")
    return "".join(directives) + " ".join(emphasized)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Design a new voice using VoxCPM2 voice design.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--voice-name", required=True,
                    help="Slug for the voice, e.g. 'Drill_Sergeant'. Becomes the library folder name.")
    ap.add_argument("--voice-fantasy", default="",
                    help="Concrete voice description (age/gender/timbre/accent). 1st () directive.")
    ap.add_argument("--emotion", default="",
                    help="Style/energy directive. 2nd () directive.")
    ap.add_argument("--no-chinese-hype", action="store_true",
                    help="Skip the Chinese emotion directive (on by default).")
    ap.add_argument("--takes", type=int, default=1,
                    help="Number of independent renders (default 1). Each take varies stochastically.")
    ap.add_argument("--lines", nargs="+", default=None,
                    help="Override the three test sentences (default: Harvard sentences).")
    ap.add_argument("--cfg-value", type=float, default=2.0,
                    help="VoxCPM guidance (default 2.0 — README-evaluated).")
    ap.add_argument("--inference-timesteps", type=int, default=10,
                    help="Diffusion steps (default 10 — README-evaluated).")
    ap.add_argument("--output-dir", type=Path, default=None,
                    help="Override output dir. By default writes to the library at "
                         "~/voxcpm-voice/voices/<voice_name>/samples/.")
    ap.add_argument("--skip-padding", action="store_true",
                    help="Skip inter-sentence silence padding.")
    ap.add_argument("--save-take", type=int, default=None,
                    help="After generation, promote samples/t<N>.wav to reference.wav immediately.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print composed text and target paths without invoking the model.")
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    slug = slugify(args.voice_name)
    lines = args.lines if args.lines else DEFAULT_LINES
    text = build_text(
        lines=lines,
        voice_fantasy=args.voice_fantasy,
        emotion=args.emotion,
        chinese_hype=not args.no_chinese_hype,
    )

    out_dir = args.output_dir if args.output_dir is not None else samples_dir(slug)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.output_dir is None:
        # Clear stale samples before re-rolling. Leaves reference.wav and lines/ untouched.
        for old in out_dir.glob("t*.wav"):
            old.unlink()

    take_paths = [out_dir / f"t{i}.wav" for i in range(1, args.takes + 1)]

    print(f"[voxcpm-voice] composed text:\n  {text}\n", flush=True)
    print(f"[voxcpm-voice] takes: {args.takes}  cfg: {args.cfg_value}  "
          f"timesteps: {args.inference_timesteps}", flush=True)
    print(f"[voxcpm-voice] writing takes to {out_dir}:")
    for p in take_paths:
        print(f"  {p.name}")

    if args.dry_run:
        print("\n[voxcpm-voice] --dry-run set; not generating.")
        return

    from voxcpm import VoxCPM
    import soundfile as sf
    import numpy as np

    print("\n[voxcpm-voice] loading VoxCPM2 (first run downloads ~2GB weights)...", flush=True)
    t0 = time.time()
    model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
    sr = model.tts_model.sample_rate
    print(f"[voxcpm-voice] model ready in {time.time() - t0:.1f}s  sr={sr}", flush=True)

    for i, out_path in enumerate(take_paths, 1):
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

    # Save metadata only when writing into the library.
    if args.output_dir is None:
        meta = VoiceMeta(
            name=slug,
            voice_fantasy=args.voice_fantasy,
            emotion=args.emotion,
            chinese_hype=not args.no_chinese_hype,
            cfg_value=args.cfg_value,
            inference_timesteps=args.inference_timesteps,
            lines=lines,
        )
        try:
            prior = VoiceMeta.load(slug)
            meta.reference_take = prior.reference_take
            meta.created_at = prior.created_at
        except FileNotFoundError:
            pass
        meta_path = meta.save()
        print(f"\n[voxcpm-voice] wrote metadata -> {meta_path}", flush=True)

    if args.save_take is not None:
        ref = promote_take(slug, args.save_take)
        meta = VoiceMeta.load(slug)
        meta.reference_take = args.save_take
        meta.save()
        print(f"[voxcpm-voice] promoted take {args.save_take} -> {ref}", flush=True)

    print(f"\n[voxcpm-voice] done. Listen, then pick a take with:")
    print(f"  save_take.py --name {slug} --take <1..{args.takes}>")


if __name__ == "__main__":
    main()
