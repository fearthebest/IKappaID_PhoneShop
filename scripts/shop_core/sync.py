"""Copy phoneshop list files to every known IKappaID Phone Shop location."""

from __future__ import annotations

import shutil
from pathlib import Path

from .discover import discover_phoneshop_locations

LIST_FILES = (
    "buy_list.txt",
    "sell_list.txt",
    "currency_list.txt",
    "vehicle_list.txt",
    "costume_list.txt",
)


def sync_phoneshop_lists(
    source: Path,
    tool_root: Path | None = None,
) -> list[tuple[Path, list[str]]]:
    """Copy list files from source to all other discovered phoneshop folders."""
    source = source.resolve()
    if not source.is_dir():
        raise FileNotFoundError(f"Source folder not found: {source}")

    results: list[tuple[Path, list[str]]] = []
    for loc in discover_phoneshop_locations(tool_root):
        dest = loc.path.resolve()
        if dest == source:
            continue
        copied: list[str] = []
        dest.mkdir(parents=True, exist_ok=True)
        for name in LIST_FILES:
            src_file = source / name
            if not src_file.is_file():
                continue
            shutil.copy2(src_file, dest / name)
            copied.append(name)
        if copied:
            results.append((dest, copied))
    return results


def find_latest_backup(path: Path) -> Path | None:
    """Newest buy_list.txt.bak.* next to path."""
    parent = path.parent
    stem = path.name
    candidates = sorted(parent.glob(f"{stem}.bak.*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def restore_from_backup(path: Path) -> Path | None:
    bak = find_latest_backup(path)
    if not bak:
        return None
    shutil.copy2(bak, path)
    return bak
