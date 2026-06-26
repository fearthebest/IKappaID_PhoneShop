#!/usr/bin/env python3
"""Launch IKappaID Phone Shop List Editor (Workshop-safe — no .bat)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    req = HERE / "requirements.txt"
    if req.is_file():
        subprocess.call(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(req)],
            cwd=str(HERE),
        )
    subprocess.check_call([sys.executable, str(HERE / "main.py")], cwd=str(HERE))


if __name__ == "__main__":
    main()
