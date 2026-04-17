#!/usr/bin/env python3
"""Generate new voicelines in a saved voice using VoxCPM Ultimate Cloning.

Two modes:

  1. Single line (or multi-line one-shot):
        speak.py --voice Drill_Sergeant --text "Get your gear and move out!"
        speak.py --voice Drill_Sergeant --lines "Line one." "Line two."

  2. YAML batch (many lines, optionally across multiple voices):
        speak.py --yaml voicelines.yaml

  YAML schema:
      voice: Drill_Sergeant           # default voice for all lines
      batch: training-vo              # optional — lines go to lines/<batch>/
      takes: 1                        # optional per-batch default

      lines:
        - "Get your gear and move out!"          # plain string → uses voice: above
        - text: "Show me some hustle!"
          takes: 2
        - voice: Arena_PA                         # override voice per line
          text: "DOUBLE KILL!"

Output:
    ~/voxcpm-voice/voices/<voice>/lines/[<batch>/]<slug>[_tN].wav

Uses Ultimate Cloning: reference.wav is passed as both reference_wav_path AND
prompt_wav_path, with prompt_text from voice.json — VoxCPM uses the text-audio
alignment to reproduce the voice with higher fidelity than plain clone mode.
"""
from __future__ import annotations
import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _library import (  # noqa: E402
    VoiceMeta,
    lines_dir,
    reference_path,
    slugify,
    slugify_short,
)
from _silence import pad_silences  # noqa: E402

os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")


@dataclass
class LineJob:
    voice: str
    text: str
    batch: str | None = None
    takes: int = 1
    direction: str = ""  # optional (direction) directive prepended to text



def parse_yaml(path: Path) -> list[LineJob]:
    import yaml

    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise SystemExit(f"YAML at {path} must be a dict with a 'lines' key.")

    default_voice = data.get("voice")
    default_batch = data.get("batch")
    default_takes = int(data.get("takes", 1))
    default_direction = data.get("direction", "")

    raw_lines = data.get("lines")
    if not raw_lines:
        raise SystemExit(f"YAML at {path} has no 'lines'.")

    jobs: list[LineJob] = []
    for i, item in enumerate(raw_lines):
        if isinstance(item, str):
            entry = {"text": item}
        elif isinstance(item, dict):
            entry = dict(item)
        else:
            raise SystemExit(f"Line {i}: must be a string or a mapping, got {type(item).__name__}")

        if "text" not in entry:
            raise SystemExit(f"Line {i}: missing 'text'")

        voice = entry.get("voice", default_voice)
        if not voice:
            raise SystemExit(f"Line {i}: no voice specified and no top-level 'voice:' default set")

        jobs.append(LineJob(
            voice=slugify(voice),
            text=str(entry["text"]).strip(),
            batch=entry.get("batch", default_batch),
            takes=int(entry.get("takes", default_takes)),
            direction=str(entry.get("direction", default_direction)).strip(),
        ))
    return jobs


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Generate voicelines in a saved voice using VoxCPM Ultimate Cloning.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--voice", help="Saved voice name. Combine with --text or --lines.")
    src.add_argument("--yaml", type=Path, help="YAML batch file (see module docstring for schema).")

    ap.add_argument("--text", help="Single line to speak (for --voice mode).")
    ap.add_argument("--lines", nargs="+", help="Multiple lines to speak (one WAV per line).")
    ap.add_argument("--batch", default=None,
                    help="Group output under lines/<batch>/ (for --voice mode). YAML can set this too.")
    ap.add_argument("--output-dir", type=Path, default=None,
                    help="Write rendered WAVs here instead of the user library. "
                         "Use this when rendering into a project's vo/audio folder. "
                         "Layout becomes <output-dir>/<voice>/[<batch>/]<slug>.wav.")
    ap.add_argument("--direction", default="",
                    help="(direction) directive prepended to each line — e.g. 'slightly faster, angry'. "
                         "Steers delivery via VoxCPM's Controllable Cloning. Changes timbre/energy; use "
                         "sparingly for pure reproduction.")
    ap.add_argument("--takes", type=int, default=1, help="Takes per line (default 1).")
    ap.add_argument("--cfg-value", type=float, default=2.0, help="VoxCPM guidance (default 2.0).")
    ap.add_argument("--inference-timesteps", type=int, default=10,
                    help="Diffusion steps (default 10).")
    ap.add_argument("--skip-padding", action="store_true",
                    help="Skip inter-sentence silence padding.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print target paths without generating.")
    return ap.parse_args()


def build_jobs(args: argparse.Namespace) -> list[LineJob]:
    if args.yaml:
        return parse_yaml(args.yaml)

    if not (args.text or args.lines):
        raise SystemExit("--voice mode requires --text or --lines")

    texts = args.lines if args.lines else [args.text]
    return [
        LineJob(
            voice=slugify(args.voice),
            text=t.strip(),
            batch=args.batch,
            takes=args.takes,
            direction=args.direction.strip(),
        )
        for t in texts if t.strip()
    ]


def target_paths(job: LineJob, output_override: Path | None = None) -> list[Path]:
    if output_override is not None:
        base = output_override / slugify(job.voice)
        if job.batch:
            base = base / slugify(job.batch)
    else:
        base = lines_dir(job.voice, job.batch)
    stem = slugify_short(job.text)
    if job.takes == 1:
        return [base / f"{stem}.wav"]
    return [base / f"{stem}_t{i}.wav" for i in range(1, job.takes + 1)]


def main() -> None:
    args = parse_args()
    jobs = build_jobs(args)

    # Validate every voice referenced has a reference.wav before loading the model.
    voices_used: dict[str, VoiceMeta] = {}
    for job in jobs:
        if job.voice in voices_used:
            continue
        try:
            meta = VoiceMeta.load(job.voice)
        except FileNotFoundError:
            raise SystemExit(f"Voice '{job.voice}' not found in the library.")
        ref = reference_path(job.voice)
        if not ref.is_file():
            raise SystemExit(
                f"Voice '{job.voice}' has no reference.wav yet. "
                f"Run save_take.py --name {job.voice} --take <N> first."
            )
        voices_used[job.voice] = meta

    output_override = args.output_dir.expanduser().resolve() if args.output_dir else None
    if output_override:
        print(f"[speak] writing into project at {output_override}", flush=True)
    print(f"[speak] {len(jobs)} line(s) across {len(voices_used)} voice(s)", flush=True)
    for job in jobs:
        for p in target_paths(job, output_override):
            p.parent.mkdir(parents=True, exist_ok=True)
            print(f"  {job.voice:20s}  {p}")

    if args.dry_run:
        print("\n[speak] --dry-run set; not generating.")
        return

    from voxcpm import VoxCPM
    import soundfile as sf
    import numpy as np

    print("\n[speak] loading VoxCPM2...", flush=True)
    t0 = time.time()
    model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
    sr = model.tts_model.sample_rate
    print(f"[speak] model ready in {time.time() - t0:.1f}s  sr={sr}", flush=True)

    total_wall = 0.0
    for job in jobs:
        meta = voices_used[job.voice]
        ref = reference_path(job.voice)
        # Ultimate Cloning if we have a transcript, otherwise Controllable Cloning.
        prompt_text = " ".join(line.strip() for line in meta.lines if line.strip())

        spoken = f"({job.direction}){job.text}" if job.direction else job.text

        kwargs = {
            "text": spoken,
            "cfg_value": args.cfg_value,
            "inference_timesteps": args.inference_timesteps,
            "reference_wav_path": str(ref),
        }
        if prompt_text:
            kwargs["prompt_wav_path"] = str(ref)
            kwargs["prompt_text"] = prompt_text

        for out_path in target_paths(job, output_override):
            t_start = time.time()
            wav = model.generate(**kwargs)
            wav_np = np.asarray(wav, dtype=np.float32)
            if not args.skip_padding:
                wav_np, _ = pad_silences(wav_np, sr)
            sf.write(str(out_path), wav_np, sr)
            dur_audio = len(wav_np) / sr
            dur_wall = time.time() - t_start
            total_wall += dur_wall
            print(f"[speak] {job.voice:20s}  {dur_wall:5.1f}s wall  "
                  f"{dur_audio:5.1f}s audio  -> {out_path.name}", flush=True)

    print(f"\n[speak] done. {total_wall:.1f}s total wall time across {len(jobs)} line(s).")


if __name__ == "__main__":
    main()
