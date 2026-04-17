#!/usr/bin/env bash
# Thin shim — the real setup is in setup.py (cross-platform).
# Kept for backward compat with older docs that referenced setup.sh.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
    for candidate in python3.11 python3.10 python3 python; do
        if command -v "$candidate" >/dev/null 2>&1; then
            PY="$candidate"
            break
        fi
    done
fi
if [ -z "$PY" ]; then
    echo "[setup.sh] no Python 3.10+ found on PATH. Install Python and retry."
    exit 1
fi

exec "$PY" "$HERE/setup.py" "$@"
