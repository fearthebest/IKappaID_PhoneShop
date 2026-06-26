"""Prepare Workshop upload folder: release lists, strip dev files, ensure B42 common/."""

from __future__ import annotations

import shutil
from pathlib import Path

WORKSHOP = Path(r"c:\Users\mpass\Zomboid\Workshop\IKappaID_PhoneShop")
DEV_ROOT = Path(__file__).resolve().parents[1]
MOD_PKG = WORKSHOP / "Contents" / "mods" / "IKappaID_PhoneShop"
PHONESHOP = MOD_PKG / "42" / "media" / "phoneshop"

STRIP_FROM_PHONESHOP = (
    "SHOP_GUIDE.txt",
    "SHOP_GUIDE.pdf",
)

STRIP_GLOBS = ("*.bak.*", "*.pre_restore.*")

# Steam Workshop blocks: .bat .exe .dll .sh .so .zip etc. — List Editor ships via GitHub only.
WORKSHOP_FORBIDDEN_SUFFIXES = (
    ".bat",
    ".exe",
    ".dll",
    ".sh",
    ".so",
    ".zip",
    ".app",
    ".dylib",
)


def strip_phoneshop_dev() -> None:
    for name in STRIP_FROM_PHONESHOP:
        path = PHONESHOP / name
        if path.is_file():
            path.unlink()
    if (PHONESHOP / ".phoneshop_editor").is_dir():
        shutil.rmtree(PHONESHOP / ".phoneshop_editor")
    for pattern in STRIP_GLOBS:
        for path in PHONESHOP.glob(pattern):
            path.unlink()


def ensure_common_folder() -> None:
    """B42 requires common/ even when empty — mod may not load without it (PZwiki)."""
    common = MOD_PKG / "common"
    common.mkdir(parents=True, exist_ok=True)
    dev_common = DEV_ROOT / "PhoneShop_Workshop" / "Contents" / "mods" / "IKappaID_PhoneShop" / "common"
    dev_common.mkdir(parents=True, exist_ok=True)


def remove_list_editor_from_package() -> None:
    """List Editor cannot ship on Workshop (forbidden file types). GitHub only."""
    for path in (WORKSHOP / "ListEditor", MOD_PKG / "ListEditor"):
        if path.is_dir():
            shutil.rmtree(path)


def assert_no_forbidden_upload_files() -> None:
    contents = WORKSHOP / "Contents"
    if not contents.is_dir():
        return
    bad: list[str] = []
    for path in contents.rglob("*"):
        if path.is_file() and path.suffix.lower() in WORKSHOP_FORBIDDEN_SUFFIXES:
            bad.append(str(path.relative_to(WORKSHOP)))
    if bad:
        raise SystemExit(
            "Workshop upload blocked — forbidden files in Contents/:\n  "
            + "\n  ".join(sorted(bad))
        )


def main() -> None:
    if not WORKSHOP.is_dir():
        raise SystemExit(f"Workshop folder missing: {WORKSHOP}")
    remove_list_editor_from_package()
    strip_phoneshop_dev()
    ensure_common_folder()
    assert_no_forbidden_upload_files()
    print(f"Workshop ready -> {WORKSHOP}")
    print("List Editor (GitHub only) -> tools/ShopListEditor/ in dev repo")


if __name__ == "__main__":
    main()
