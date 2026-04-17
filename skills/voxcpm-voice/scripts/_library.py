"""Shared helpers for the voxcpm-voice library layout.

Library layout:
    ~/voxcpm-voice/voices/<voice_name>/
        voice.json            metadata — prompt, sentences, reference_take, timestamps
        reference.wav         the chosen take, used for cloning (only set by save_take)
        samples/              voice-design rolls from generate_voice (overwritten on re-roll)
            t1.wav
            t2.wav
            ...
        lines/                cloned-voice voicelines from speak (accumulates; never blown away)
            [<batch>/]<slug>.wav

Re-rolling a design overwrites samples/ but leaves reference.wav and lines/ alone.
"""
from __future__ import annotations

import json
import re
import shutil
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path

LIBRARY_ROOT = Path.home() / "voxcpm-voice" / "voices"
DEFAULT_LINES = [
    "The birch canoe slid on the smooth planks.",
    "Glue the sheet to the dark blue background.",
    "It's easy to tell the depth of a well.",
]


def slugify(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_")
    return cleaned or "voice"


def slugify_short(text: str, maxlen: int = 48) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return s[:maxlen] or "line"


def voice_dir(name: str) -> Path:
    return LIBRARY_ROOT / slugify(name)


@dataclass
class VoiceMeta:
    """On-disk schema for voices/<name>/voice.json.

    A voice can arrive two ways:
      - designed: generate_voice.py rolled it from a text description. Samples
        live in samples/; one is promoted to reference.wav.
      - imported: import_voice.py took an external audio file and wrote it
        directly to reference.wav. No samples. `source_audio` records where it
        came from (for traceability; the skill doesn't need it at runtime).
    """
    name: str
    voice_fantasy: str = ""
    emotion: str = ""
    chinese_hype: bool = True
    cfg_value: float = 2.0
    inference_timesteps: int = 10
    lines: list[str] = field(default_factory=list)   # transcript of reference.wav
    reference_take: int | None = None                 # which samples/t<N>.wav was promoted
    imported: bool = False                            # True if from import_voice.py
    source_audio: str = ""                            # original path (imports only)
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def load(cls, name: str) -> "VoiceMeta":
        path = voice_dir(name) / "voice.json"
        if not path.is_file():
            raise FileNotFoundError(f"No voice named '{name}' in library at {path.parent}")
        data = json.loads(path.read_text())
        # Drop unknown keys so older/newer schemas don't crash __init__.
        allowed = {f for f in cls.__dataclass_fields__}
        data = {k: v for k, v in data.items() if k in allowed}
        return cls(**data)

    def save(self) -> Path:
        d = voice_dir(self.name)
        d.mkdir(parents=True, exist_ok=True)
        now = time.strftime("%Y-%m-%dT%H:%M:%S%z") or time.strftime("%Y-%m-%dT%H:%M:%S")
        if not self.created_at:
            self.created_at = now
        self.updated_at = now
        path = d / "voice.json"
        path.write_text(json.dumps(asdict(self), indent=2) + "\n")
        return path


def list_voices() -> list[VoiceMeta]:
    if not LIBRARY_ROOT.is_dir():
        return []
    out = []
    for child in sorted(LIBRARY_ROOT.iterdir()):
        if not child.is_dir():
            continue
        meta_path = child / "voice.json"
        if not meta_path.is_file():
            continue
        try:
            out.append(VoiceMeta(**json.loads(meta_path.read_text())))
        except Exception:
            continue
    return out


def has_reference(name: str) -> bool:
    return (voice_dir(name) / "reference.wav").is_file()


def reference_path(name: str) -> Path:
    return voice_dir(name) / "reference.wav"


def samples_dir(name: str) -> Path:
    return voice_dir(name) / "samples"


def lines_dir(name: str, batch: str | None = None) -> Path:
    base = voice_dir(name) / "lines"
    return base / slugify(batch) if batch else base


def promote_take(name: str, take_index: int) -> Path:
    """Copy samples/t<take_index>.wav to reference.wav. Returns the reference path."""
    src = samples_dir(name) / f"t{take_index}.wav"
    if not src.is_file():
        raise FileNotFoundError(f"No take {take_index} at {src}")
    ref = reference_path(name)
    ref.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, ref)
    return ref
