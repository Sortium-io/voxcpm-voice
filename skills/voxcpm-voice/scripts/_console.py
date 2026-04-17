"""Windows console-encoding fix.

The plugin's scripts print em dashes, Chinese style directives, and tqdm block
glyphs. On Windows, the default console code page is cp1252 which can't
encode any of that — the first print() that contains a non-ASCII byte blows
up with UnicodeEncodeError. Users can work around it via PYTHONIOENCODING or
PYTHONUTF8, but the right fix is for the scripts to make themselves safe.

Import this module *first* in any script that prints. No-op on non-Windows
platforms (stdout is already UTF-8 there).
"""
from __future__ import annotations
import sys


def _reconfigure_if_needed() -> None:
    if sys.platform != "win32":
        return
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            # Detached stream, closed stream, or already UTF-8 — nothing we can do.
            pass


_reconfigure_if_needed()
