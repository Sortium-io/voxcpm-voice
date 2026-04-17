#!/usr/bin/env python3
"""Initialize voxcpm-voice scaffolding inside a project directory.

Creates a `vo/` tree at the project root so rendered voicelines land alongside
the code they're for, instead of buried in ~/voxcpm-voice/voices/<voice>/lines.

    init_project.py                      # uses current working directory
    init_project.py --path ~/projects/my-game

Layout:
    <project>/vo/
    ├── README.md              # notes on what lives here and how to use it
    ├── audio/                 # speak.py writes rendered WAVs here
    │   └── .gitkeep
    └── scripts/               # YAML batches for speak.py --yaml
        └── example.yaml       # starter template, copied from the plugin

Idempotent — running twice is safe. Skips files that already exist.
"""
from __future__ import annotations
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _console  # noqa: F401, E402  — reconfigures stdout to UTF-8 on Windows

TEMPLATE_RELATIVE = "../templates/voicelines.yaml"

VO_README = """# VO directory

Rendered voicelines for this project live here. Layout:

- `audio/` — WAV files rendered by the voxcpm-voice skill. Pass
  `--output-dir ./vo/audio` to `speak.py` (or tell Claude "render into this
  project's vo folder") and your lines land here instead of in the user-wide
  library at `~/voxcpm-voice/voices/<voice>/lines/`.
- `scripts/` — YAML batches for `speak.py --yaml`. Check these into git so
  your team can render the same VO set on any machine.

Your voice library itself (voice.json, reference.wav, design samples) lives at
`~/voxcpm-voice/voices/`. That's machine-wide and shared across every project
that uses the skill. This `vo/` tree is only for *this project's* rendered
output and the scripts that produce it.

## Typical flow

1. Design or import a voice once (at the user level, not per-project):
   ```
   Use voxcpm-voice to make me a drill sergeant voice.
   ```
2. Write a YAML batch in `vo/scripts/` listing the lines you need.
3. Ask Claude to render it into this project's vo/audio:
   ```
   Render vo/scripts/my-vo.yaml into this project.
   ```
4. Commit the YAML scripts. Gitignore `vo/audio/` if the WAVs are too big
   to check in.
"""

EXAMPLE_FALLBACK = """# Minimal starter — see full template at
# ${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/templates/voicelines.yaml
voice: CHANGE_ME          # a voice you've saved in ~/voxcpm-voice/voices/
batch: example            # optional — groups output under audio/<batch>/
lines:
  - "Replace this line with something your project actually needs."
"""


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Scaffold a voxcpm-voice vo/ folder inside a project.",
    )
    ap.add_argument("--path", type=Path, default=Path.cwd(),
                    help="Project root (default: current working directory).")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite existing starter files (keeps your custom files untouched).")
    return ap.parse_args()


def locate_template() -> Path | None:
    """Find the plugin-bundled voicelines.yaml template.

    Prefers a sibling templates/ dir to this script. Falls back to the
    CLAUDE_PLUGIN_ROOT env var if set.
    """
    here = Path(__file__).resolve().parent
    local = (here / TEMPLATE_RELATIVE).resolve()
    if local.is_file():
        return local
    import os
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin_root:
        candidate = Path(plugin_root) / "skills" / "voxcpm-voice" / "templates" / "voicelines.yaml"
        if candidate.is_file():
            return candidate
    return None


def write_if_absent(path: Path, content: str, force: bool, label: str) -> None:
    if path.exists() and not force:
        print(f"[init_project] keeping existing {label} at {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"[init_project] wrote {label} -> {path}")


def main() -> None:
    args = parse_args()
    project = args.path.expanduser().resolve()
    if project.exists() and not project.is_dir():
        sys.exit(f"Project path exists but is a file, not a directory: {project}")
    if not project.exists():
        project.mkdir(parents=True, exist_ok=True)
        print(f"[init_project] created project dir {project}")

    vo = project / "vo"
    audio = vo / "audio"
    scripts = vo / "scripts"

    print(f"[init_project] setting up {vo}")
    for d in (vo, audio, scripts):
        d.mkdir(parents=True, exist_ok=True)

    # .gitkeep so audio/ stays in the tree even when empty
    write_if_absent(audio / ".gitkeep", "", args.force, "audio/.gitkeep")

    # README for the vo/ folder
    write_if_absent(vo / "README.md", VO_README, args.force, "vo/README.md")

    # Starter YAML — copy from the plugin's template if available, else fallback
    example = scripts / "example.yaml"
    if not example.exists() or args.force:
        template = locate_template()
        if template is not None:
            shutil.copy2(template, example)
            print(f"[init_project] wrote starter -> {example}  (from {template.name})")
        else:
            example.write_text(EXAMPLE_FALLBACK)
            print(f"[init_project] wrote minimal starter -> {example}  (template not found)")
    else:
        print(f"[init_project] keeping existing starter at {example}")

    print(f"\n[init_project] done. This project now has:")
    print(f"  {vo}/")
    print(f"    audio/       rendered WAVs land here")
    print(f"    scripts/     your YAML batches (example.yaml is a starting point)")
    print(f"    README.md    how to use this layout")
    print(f"\n[init_project] next up:")
    print(f"  1. Edit {example}")
    print(f"  2. Ask Claude: \"Render vo/scripts/example.yaml into this project's vo/audio.\"")
    print(f"  3. Or call speak.py directly with --yaml and --output-dir ./vo/audio")


if __name__ == "__main__":
    main()
