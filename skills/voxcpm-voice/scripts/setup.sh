#!/usr/bin/env bash
# Idempotent setup for the voxcpm-voice skill.
# Creates ~/voxcpm-voice/voxcpm-venv and installs the VoxCPM dependencies.
# Exits immediately if already installed.

set -euo pipefail

WORK_DIR="$HOME/voxcpm-voice"
VENV="$WORK_DIR/voxcpm-venv"
PYTHON="$VENV/bin/python"

if [ -x "$PYTHON" ] && "$PYTHON" -c "import voxcpm, soundfile, numpy" 2>/dev/null; then
    echo "[voxcpm-voice setup] already installed at $VENV"
    exit 0
fi

mkdir -p "$WORK_DIR/outputs"

if [ ! -x "$PYTHON" ]; then
    echo "[voxcpm-voice setup] creating venv at $VENV"
    if command -v python3.11 >/dev/null 2>&1; then
        python3.11 -m venv "$VENV"
    elif command -v python3.10 >/dev/null 2>&1; then
        python3.10 -m venv "$VENV"
    else
        python3 -m venv "$VENV"
    fi
fi

echo "[voxcpm-voice setup] installing packages (this takes a couple of minutes on first run)"
"$PYTHON" -m pip install --upgrade pip --quiet
"$PYTHON" -m pip install --quiet voxcpm soundfile torchaudio numpy pyyaml

echo "[voxcpm-voice setup] done — venv at $VENV"
echo "[voxcpm-voice setup] model weights (~2GB) will download on first generate call"
