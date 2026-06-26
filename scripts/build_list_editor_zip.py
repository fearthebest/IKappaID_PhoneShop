"""Zip Shop List Editor for GitHub Releases (includes shop_core + run.bat)."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

DEV_ROOT = Path(__file__).resolve().parents[1]
EDITOR_SRC = DEV_ROOT / "tools" / "ShopListEditor"
SHOP_CORE_SRC = DEV_ROOT / "scripts" / "shop_core"
OUT_DIR = DEV_ROOT / "dist"
ZIP_NAME = "IKappaID_PhoneShop_ListEditor.zip"

EDITOR_FILES = (
    "main.py",
    "theme.py",
    "launch.py",
    "run.bat",
    "requirements.txt",
    "START_HERE.txt",
    "README.md",
)


def main() -> None:
    if not EDITOR_SRC.is_dir():
        raise SystemExit(f"Missing: {EDITOR_SRC}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = OUT_DIR / ZIP_NAME
    if zip_path.is_file():
        zip_path.unlink()

    staging = OUT_DIR / "_list_editor_staging"
    if staging.is_dir():
        shutil.rmtree(staging)
    staging.mkdir()

    for name in EDITOR_FILES:
        src = EDITOR_SRC / name
        if src.is_file():
            shutil.copy2(src, staging / name)
    shutil.copytree(
        SHOP_CORE_SRC,
        staging / "shop_core",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (staging / "config.json").write_text("{}\n", encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(staging).as_posix())

    shutil.rmtree(staging)
    print(f"Created -> {zip_path}")
    print("Upload this zip to GitHub Releases and link it from the Workshop description.")


if __name__ == "__main__":
    main()
