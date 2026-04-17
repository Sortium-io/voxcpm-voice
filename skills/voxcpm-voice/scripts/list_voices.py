#!/usr/bin/env python3
"""Print a human-readable listing of every voice in the library."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _library import LIBRARY_ROOT, has_reference, list_voices, samples_dir, lines_dir  # noqa: E402


def count_wavs(d: Path) -> int:
    return len(list(d.rglob("*.wav"))) if d.exists() else 0


def main() -> None:
    voices = list_voices()
    if not voices:
        print(f"[list_voices] no voices in {LIBRARY_ROOT}")
        print(f"[list_voices] run generate_voice.py to design one.")
        return

    print(f"[list_voices] {len(voices)} voice(s) in {LIBRARY_ROOT}\n")
    for v in voices:
        has_ref = has_reference(v.name)
        has_transcript = bool(v.lines and any(line.strip() for line in v.lines))
        if v.imported:
            mode = "imported (Ultimate Cloning)" if has_transcript else "imported (Controllable Cloning)"
        else:
            mode = "designed"
        if not has_ref:
            mode += " — ✗ no reference.wav yet"
            if not v.imported:
                mode += " (run save_take.py)"

        n_samples = count_wavs(samples_dir(v.name))
        n_lines = count_wavs(lines_dir(v.name))
        print(f"  {v.name}")
        print(f"    mode     : {mode}")
        if v.voice_fantasy:
            print(f"    fantasy  : {v.voice_fantasy}")
        if v.emotion:
            print(f"    emotion  : {v.emotion}")
        if v.imported and v.source_audio:
            print(f"    source   : {v.source_audio}")
        if v.imported:
            print(f"    lines    : {n_lines} file(s) generated")
        else:
            print(f"    takes    : {n_samples} sample(s)   lines: {n_lines} file(s)")
        if v.reference_take is not None:
            print(f"    reference: take {v.reference_take}")
        print()


if __name__ == "__main__":
    main()
