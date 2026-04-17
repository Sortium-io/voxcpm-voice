#!/usr/bin/env python3
"""Import an existing audio clip as a voice in the library.

The clip becomes the voice's reference.wav; speak.py can then generate new
lines in that voice. Provide a transcript for Ultimate Cloning (maximum
fidelity reproduction); leave it off for Controllable Cloning (timbre locked,
delivery a bit more flexible).

    import_voice.py --voice-name Narrator_Sam --audio sam.mp3
    import_voice.py --voice-name Narrator_Sam --audio sam.mp3 --text "The transcript of sam.mp3 goes here."
    import_voice.py --voice-name Narrator_Sam --audio sam.mp3 --text-file sam.txt

Does NOT load VoxCPM — this is pure file preprocessing (mono conversion +
25-second trim) plus metadata. Use speak.py afterward to generate voicelines.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _library import (  # noqa: E402
    VoiceMeta,
    reference_path,
    slugify,
    voice_dir,
)

MAX_REF_SECONDS = 25
SUPPORTED_SUFFIXES = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".opus", ".aac", ".aif", ".aiff"}


def load_transcript(args: argparse.Namespace) -> str:
    if args.text and args.text_file:
        raise SystemExit("Pass --text OR --text-file, not both.")
    if args.text:
        return args.text.strip()
    if args.text_file:
        path = Path(args.text_file)
        if not path.is_file():
            raise SystemExit(f"Transcript file not found: {path}")
        return path.read_text(encoding="utf-8").strip()
    return ""


def preprocess_audio(src: Path, dest: Path, max_seconds: int) -> tuple[int, float]:
    """Convert to mono WAV, trim to max_seconds, write to dest. Returns (sr, duration_secs)."""
    import torchaudio

    wav, sr = torchaudio.load(str(src))
    if wav.shape[0] > 1:
        wav = wav.mean(dim=0, keepdim=True)
    max_frames = max_seconds * sr
    if wav.shape[1] > max_frames:
        wav = wav[:, :max_frames]
    dest.parent.mkdir(parents=True, exist_ok=True)
    torchaudio.save(str(dest), wav, sr)
    return sr, wav.shape[1] / sr


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Import an external audio clip as a voice in the library.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--voice-name", required=True,
                    help="Slug for the voice, e.g. 'Narrator_Sam'.")
    ap.add_argument("--audio", required=True, type=Path,
                    help="Path to the source audio file (wav/flac/mp3/m4a/ogg/opus/aac/aiff).")
    ap.add_argument("--text", default=None,
                    help="Transcript of the audio (literal). Enables Ultimate Cloning.")
    ap.add_argument("--text-file", default=None,
                    help="Path to a file containing the transcript. Alternative to --text.")
    ap.add_argument("--voice-fantasy", default="",
                    help="Optional descriptor saved to voice.json — documentation only.")
    ap.add_argument("--emotion", default="",
                    help="Optional emotional descriptor — documentation only.")
    ap.add_argument("--max-seconds", type=int, default=MAX_REF_SECONDS,
                    help=f"Trim audio to this length (default {MAX_REF_SECONDS}s). "
                         "VoxCPM uses the reference clip as a timbre/style anchor — "
                         "long clips don't improve cloning and slow things down.")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite an existing voice with the same name.")
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    slug = slugify(args.voice_name)
    src = args.audio.expanduser().resolve()
    if not src.is_file():
        raise SystemExit(f"Source audio not found: {src}")
    if src.suffix.lower() not in SUPPORTED_SUFFIXES:
        print(f"[import_voice] warning: {src.suffix} isn't a typical audio suffix; "
              f"trying anyway via torchaudio", file=sys.stderr)

    dest_dir = voice_dir(slug)
    ref = reference_path(slug)
    if ref.is_file() and not args.force:
        raise SystemExit(
            f"Voice '{slug}' already has a reference.wav at {ref}. "
            f"Pass --force to overwrite, or pick a different --voice-name."
        )
    dest_dir.mkdir(parents=True, exist_ok=True)

    transcript = load_transcript(args)

    print(f"[import_voice] {src}")
    sr, dur = preprocess_audio(src, ref, args.max_seconds)
    print(f"[import_voice] wrote {ref}  ({dur:.1f}s @ {sr} Hz)")

    lines = [line.strip() for line in transcript.replace("\n", " ").split(".") if line.strip()]
    # Re-append periods we stripped during split (skip the last empty tail).
    lines = [f"{line}." if not line.endswith(('!', '?', '.')) else line for line in lines]

    meta = VoiceMeta(
        name=slug,
        voice_fantasy=args.voice_fantasy,
        emotion=args.emotion,
        lines=lines,
        imported=True,
        source_audio=str(src),
    )
    try:
        prior = VoiceMeta.load(slug)
        meta.created_at = prior.created_at
    except FileNotFoundError:
        pass
    meta_path = meta.save()
    print(f"[import_voice] wrote {meta_path}")

    if transcript:
        print(f"[import_voice] transcript provided ({len(transcript)} chars) — speak.py will use Ultimate Cloning.")
    else:
        print(f"[import_voice] no transcript — speak.py will use Controllable Cloning (timbre locks, "
              f"delivery a bit more flexible). Pass --text next time for max fidelity.")

    print(f"\n[import_voice] '{slug}' is ready. Generate lines with:")
    print(f"  speak.py --voice {slug} --text \"...\"")


if __name__ == "__main__":
    main()
