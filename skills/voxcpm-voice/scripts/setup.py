#!/usr/bin/env python3
"""Cross-platform setup for the voxcpm-voice skill.

Creates a Python venv at ~/voxcpm-voice/voxcpm-venv and installs VoxCPM deps.
Idempotent — safe to run twice; exits immediately if everything is already in
place.

Platform handling:
  - macOS (darwin): default torch wheels (MPS on Apple Silicon, CPU on Intel).
  - Linux: CUDA 12.1 wheels if nvidia-smi is detected, else CPU wheels.
  - Windows: CUDA 12.1 wheels if nvidia-smi is detected, else CPU wheels.

Run with any system Python ≥ 3.10:
    python3 setup.py            # macOS / Linux
    python   setup.py            # Windows

The skill invokes this directly; users normally never run it.
"""
from __future__ import annotations
import os
import platform
import shutil
import subprocess
import sys
import venv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _console  # noqa: F401, E402  — reconfigures stdout to UTF-8 on Windows

WORK_DIR = Path.home() / "voxcpm-voice"
VENV_DIR = WORK_DIR / "voxcpm-venv"
OUTPUTS_DIR = WORK_DIR / "outputs"
VOICES_DIR = WORK_DIR / "voices"

# pinned PyTorch CUDA index — update as the VoxCPM/torch compat matrix changes
TORCH_CUDA_INDEX = "https://download.pytorch.org/whl/cu121"

SYSTEM = platform.system().lower()   # 'darwin', 'linux', 'windows'
IS_WINDOWS = SYSTEM == "windows"
IS_DARWIN = SYSTEM == "darwin"
IS_LINUX = SYSTEM == "linux"


def venv_python(venv_dir: Path = VENV_DIR) -> Path:
    """Return the path to the venv's Python interpreter for the current platform."""
    return venv_dir / ("Scripts" if IS_WINDOWS else "bin") / ("python.exe" if IS_WINDOWS else "python")


def has_cuda() -> bool:
    """Return True if an NVIDIA GPU is present (via nvidia-smi on PATH)."""
    return shutil.which("nvidia-smi") is not None


def pkgs_already_installed(py: Path) -> bool:
    """Fast idempotency check — do the key packages already import?"""
    if not py.is_file():
        return False
    try:
        subprocess.run(
            [str(py), "-c", "import voxcpm, soundfile, torchaudio, numpy, yaml"],
            check=True, capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def create_venv() -> None:
    if venv_python().is_file():
        print(f"[setup] venv exists at {VENV_DIR}")
        return
    print(f"[setup] creating venv at {VENV_DIR}")
    VENV_DIR.parent.mkdir(parents=True, exist_ok=True)
    venv.EnvBuilder(with_pip=True, clear=False, upgrade=False).create(str(VENV_DIR))


def pip_install(py: Path, args: list[str], label: str) -> None:
    print(f"[setup] installing {label}")
    subprocess.check_call([str(py), "-m", "pip", "install", "--quiet", *args])


def find_compatible_python() -> str | None:
    """On Windows, use the `py` launcher to find Python 3.10–3.12 if the current one's too new."""
    if not IS_WINDOWS:
        return None
    py_launcher = shutil.which("py")
    if not py_launcher:
        return None
    for ver in ("3.12", "3.11", "3.10"):
        try:
            subprocess.run([py_launcher, f"-{ver}", "--version"],
                           check=True, capture_output=True)
            return f"py -{ver}"
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return None


def require_compatible_python() -> None:
    ver = sys.version.split()[0]
    if sys.version_info < (3, 10):
        sys.exit(f"[setup] Python 3.10–3.12 required. This interpreter is {ver}. "
                 f"Install a compatible Python and rerun setup.py with it.")
    if sys.version_info >= (3, 13):
        suggestion = find_compatible_python()
        msg = [f"[setup] Python 3.10–3.12 required. This interpreter is {ver}."]
        msg.append("[setup] VoxCPM depends on PyTorch, and PyTorch doesn't ship wheels for 3.13+ yet.")
        if suggestion:
            script = Path(__file__).resolve()
            msg.append(f"[setup] Found a compatible interpreter on this machine — rerun with:")
            msg.append(f'[setup]     {suggestion} "{script}"')
        elif IS_WINDOWS:
            msg.append("[setup] Install Python 3.12 and rerun with:")
            msg.append('[setup]     py -3.12 "<path-to-setup.py>"')
            if shutil.which("winget"):
                msg.append("[setup] winget is available — quickest path is:")
                msg.append("[setup]     winget install --id Python.Python.3.12 -e")
            else:
                msg.append("[setup] Get Python 3.12 from https://www.python.org/downloads/")
        else:
            msg.append("[setup] Install Python 3.12 (pyenv / conda / your OS package manager) and rerun with that interpreter.")
        sys.exit("\n".join(msg))


def main() -> None:
    print(f"[setup] platform: {SYSTEM}  python: {sys.version.split()[0]}")
    require_compatible_python()

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    VOICES_DIR.mkdir(parents=True, exist_ok=True)

    py = venv_python()
    if pkgs_already_installed(py):
        print(f"[setup] already installed at {VENV_DIR} — nothing to do.")
        return

    create_venv()
    py = venv_python()

    # Upgrade pip first so CUDA wheel resolution is modern.
    pip_install(py, ["--upgrade", "pip"], "pip (upgrade)")

    # PyTorch + torchaudio: route through the CUDA index on NVIDIA systems.
    # macOS always uses the default wheels (MPS on Apple Silicon, CPU on Intel).
    if (IS_WINDOWS or IS_LINUX) and has_cuda():
        print(f"[setup] nvidia-smi detected — installing CUDA 12.1 torch wheels")
        pip_install(py, ["torch", "torchaudio", "--index-url", TORCH_CUDA_INDEX], "torch (CUDA)")
    else:
        reason = "macOS" if IS_DARWIN else "no nvidia-smi found"
        print(f"[setup] installing default torch wheels ({reason} — CPU/MPS)")
        pip_install(py, ["torch", "torchaudio"], "torch")

    # Everything else is platform-independent.
    pip_install(py, ["voxcpm", "soundfile", "numpy", "pyyaml"], "voxcpm + deps")

    print(f"\n[setup] done. venv at {VENV_DIR}")
    print(f"[setup] model weights (~2 GB) will download on first generate call")


if __name__ == "__main__":
    main()
