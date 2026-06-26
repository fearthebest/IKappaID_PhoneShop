"""Vanilla / baseline snapshots for Phone Shop list files."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .sync import LIST_FILES

SNAPSHOT_DIRNAME = ".phoneshop_editor"
VANILLA_SUBDIR = "vanilla_baseline"
META_FILE = "meta.json"


def vanilla_dir(shop: Path) -> Path:
    return shop.resolve() / SNAPSHOT_DIRNAME / VANILLA_SUBDIR


def vanilla_meta_path(shop: Path) -> Path:
    return vanilla_dir(shop) / META_FILE


def has_vanilla_baseline(shop: Path) -> bool:
    base = vanilla_dir(shop)
    return (base / "buy_list.txt").is_file() and (base / "sell_list.txt").is_file()


def vanilla_info(shop: Path) -> dict | None:
    meta = vanilla_meta_path(shop)
    if not meta.is_file():
        if has_vanilla_baseline(shop):
            return {"saved_at": None, "note": "baseline present (no meta)"}
        return None
    return json.loads(meta.read_text(encoding="utf-8"))


def save_vanilla_baseline(shop: Path, note: str = "") -> Path:
    shop = shop.resolve()
    if not shop.is_dir():
        raise FileNotFoundError(f"Phone Shop folder not found: {shop}")
    dest = vanilla_dir(shop)
    if dest.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.move(str(dest), str(dest.parent / f"vanilla_baseline_prev_{stamp}"))
    dest.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in LIST_FILES:
        src = shop / name
        if src.is_file():
            shutil.copy2(src, dest / name)
            copied.append(name)
    if "buy_list.txt" not in copied or "sell_list.txt" not in copied:
        raise FileNotFoundError("buy_list.txt and sell_list.txt must exist in the Phone Shop folder.")
    meta = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "source": str(shop),
        "files": copied,
        "note": note.strip(),
    }
    vanilla_meta_path(shop).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return dest


def restore_vanilla_baseline(shop: Path, *, backup_current: bool = True) -> list[str]:
    shop = shop.resolve()
    src = vanilla_dir(shop)
    if not has_vanilla_baseline(shop):
        raise FileNotFoundError(
            "No vanilla baseline saved yet.\nUse “Save vanilla baseline” while lists are still good."
        )
    restored: list[str] = []
    for name in LIST_FILES:
        snap = src / name
        if not snap.is_file():
            continue
        target = shop / name
        if backup_current and target.is_file():
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(target, target.with_suffix(target.suffix + f".pre_restore.{stamp}"))
        shutil.copy2(snap, target)
        restored.append(name)
    return restored


def format_vanilla_status(shop: Path) -> str:
    info = vanilla_info(shop)
    if not info:
        return "Vanilla baseline: not saved yet — save while lists are good"
    saved = info.get("saved_at") or "unknown time"
    if saved != "unknown time" and "T" in saved:
        try:
            dt = datetime.fromisoformat(saved.replace("Z", "+00:00"))
            saved = dt.strftime("%Y-%m-%d %H:%M UTC")
        except ValueError:
            pass
    files = info.get("files") or []
    return f"Vanilla baseline: saved {saved} ({len(files)} files)"
