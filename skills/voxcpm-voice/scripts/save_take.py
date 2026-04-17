#!/usr/bin/env python3
"""Promote one of a voice's samples to its reference.wav.

    save_take.py --name Drill_Sergeant --take 2

Copies ~/voxcpm-voice/voices/Drill_Sergeant/samples/t2.wav to
~/voxcpm-voice/voices/Drill_Sergeant/reference.wav and records the choice in
voice.json so speak.py knows which take was picked.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _console  # noqa: F401, E402  — reconfigures stdout to UTF-8 on Windows
from _library import VoiceMeta, promote_take, slugify  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Promote a sample to a voice's reference.wav.")
    ap.add_argument("--name", required=True, help="Voice name (the library folder).")
    ap.add_argument("--take", type=int, required=True, help="Take number (1-based) to promote.")
    args = ap.parse_args()

    slug = slugify(args.name)
    try:
        meta = VoiceMeta.load(slug)
    except FileNotFoundError as e:
        sys.exit(str(e))

    try:
        ref = promote_take(slug, args.take)
    except FileNotFoundError as e:
        sys.exit(str(e))

    meta.reference_take = args.take
    meta.save()
    print(f"[save_take] promoted take {args.take} -> {ref}")
    print(f"[save_take] '{slug}' is now ready for speak.py")


if __name__ == "__main__":
    main()
