"""Locate IKappaID Phone Shop media/phoneshop folders on this machine."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

WORKSHOP_ITEM_ID = "3749926419"
MOD_ID = "IKappaID_PhoneShop"

# Standard layout inside a Phone Shop package.
PHONESHOP_SUFFIXES = (
    Path("Contents/mods/IKappaID_PhoneShop/42/media/phoneshop"),
    Path("mods/IKappaID_PhoneShop/42/media/phoneshop"),
    Path("IKappaID_PhoneShop/42/media/phoneshop"),
)


@dataclass(frozen=True)
class PhoneShopLocation:
    path: Path
    source: str
    score: float
    buy_mtime: float = 0.0

    @property
    def label(self) -> str:
        return f"{self.source} — {self.path}"


def _is_phoneshop_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    return (path / "buy_list.txt").is_file()


def _buy_mtime(path: Path) -> float:
    buy = path / "buy_list.txt"
    if buy.is_file():
        return buy.stat().st_mtime
    return 0.0


def _user_home() -> Path:
    return Path.home()


def _zomboid_root() -> Path | None:
    root = _user_home() / "Zomboid"
    return root if root.is_dir() else None


def _tool_dev_phoneshop(tool_root: Path | None) -> Path | None:
    if not tool_root:
        return None
    candidates = [
        # Bundled inside Contents/mods/IKappaID_PhoneShop/ListEditor (BUNDLE_ROOT = mod package)
        tool_root / "42" / "media" / "phoneshop",
        tool_root / "Contents" / "mods" / MOD_ID / "42" / "media" / "phoneshop",
        tool_root / "PhoneShop_Workshop" / "Contents" / "mods" / MOD_ID / "42" / "media" / "phoneshop",
    ]
    for path in candidates:
        if _is_phoneshop_dir(path):
            return path
    for path in candidates:
        if path.parent.parent.exists():
            return path
    return None


def _parse_libraryfolders_vdf(path: Path) -> list[Path]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    libs: list[Path] = []
    for m in re.finditer(r'"path"\s+"([^"]+)"', text):
        raw = m.group(1).replace("\\\\", "\\")
        libs.append(Path(raw))
    return libs


def _steam_library_roots() -> list[Path]:
    seen: set[str] = set()
    roots: list[Path] = []

    def add(p: Path) -> None:
        key = str(p.resolve()).lower()
        if key in seen:
            return
        if p.is_dir():
            seen.add(key)
            roots.append(p)

    for env_key in ("ProgramFiles(x86)", "ProgramFiles"):
        base = os.environ.get(env_key)
        if base:
            add(Path(base) / "Steam")
    add(_user_home() / "Steam")
    for letter in "CDEFGHBIJKLMNOPQRSTUVWXYZ":
        add(Path(f"{letter}:/SteamLibrary"))
        add(Path(f"{letter}:/Steam"))
    for steam in list(roots):
        add(steam / "steamapps")
        vdf = steam / "steamapps" / "libraryfolders.vdf"
        for lib in _parse_libraryfolders_vdf(vdf):
            add(lib)
            add(lib / "steamapps")
    return roots


def _steam_workshop_phoneshop() -> Path | None:
    for lib in _steam_library_roots():
        base = lib / "workshop" / "content" / "108600" / WORKSHOP_ITEM_ID
        for suffix in PHONESHOP_SUFFIXES:
            path = base / suffix
            if _is_phoneshop_dir(path):
                return path
            # Flat: .../3749926419/mods/IKappaID_PhoneShop/...
            flat = base / "mods" / MOD_ID / "42" / "media" / "phoneshop"
            if _is_phoneshop_dir(flat):
                return flat
    return None


def _collect_candidates(tool_root: Path | None = None) -> list[tuple[Path, str, float]]:
    """Return (path, source_label, base_priority)."""
    out: list[tuple[Path, str, float]] = []
    seen: set[str] = set()

    def add(path: Path | None, source: str, priority: float) -> None:
        if not path:
            return
        try:
            key = str(path.resolve()).lower()
        except OSError:
            return
        if key in seen:
            return
        seen.add(key)
        if _is_phoneshop_dir(path):
            out.append((path.resolve(), source, priority))

    zomboid = _zomboid_root()
    if zomboid:
        add(
            zomboid / "Workshop" / "IKappaID_PhoneShop" / "Contents" / "mods" / MOD_ID / "42" / "media" / "phoneshop",
            "Zomboid Workshop (upload)",
            100.0,
        )
        add(
            zomboid / "mods" / MOD_ID / "42" / "media" / "phoneshop",
            "Zomboid mods (local)",
            60.0,
        )
        # Any other Workshop package name containing Phone Shop
        workshop_dir = zomboid / "Workshop"
        if workshop_dir.is_dir():
            for pkg in workshop_dir.iterdir():
                if not pkg.is_dir():
                    continue
                for suffix in PHONESHOP_SUFFIXES:
                    add(pkg / suffix, f"Zomboid Workshop ({pkg.name})", 90.0)

    dev = _tool_dev_phoneshop(tool_root)
    add(dev, "Dev repo (next to tool)", 85.0)

    add(_steam_workshop_phoneshop(), "Steam Workshop cache", 70.0)

    saved = os.environ.get("PHONESHOP_LIST_DIR", "").strip()
    if saved:
        add(Path(saved), "PHONESHOP_LIST_DIR env", 95.0)

    return out


def _score(path: Path, source: str, base_priority: float, preferred: Path | None) -> PhoneShopLocation:
    score = base_priority
    mtime = _buy_mtime(path)
    if mtime:
        score += mtime / 1_000_000_000.0
    if (path / "sell_list.txt").is_file():
        score += 5.0
    if (path / "currency_list.txt").is_file():
        score += 2.0
    if preferred:
        try:
            if path.resolve() == preferred.resolve():
                score += 15.0
        except OSError:
            pass
    return PhoneShopLocation(path=path, source=source, score=score, buy_mtime=mtime)


def discover_phoneshop_locations(
    tool_root: Path | None = None,
    preferred: Path | str | None = None,
) -> list[PhoneShopLocation]:
    pref = Path(preferred) if preferred else None
    if pref and pref.is_dir() and _is_phoneshop_dir(pref):
        candidates = [(pref.resolve(), "Saved / preferred", 110.0)]
    else:
        candidates = []
    for path, source, priority in _collect_candidates(tool_root):
        if pref and path.resolve() == pref.resolve():
            continue
        candidates.append((path, source, priority))
    ranked = [_score(p, s, pr, pref) for p, s, pr in candidates]
    ranked.sort(key=lambda loc: (-loc.score, loc.source))
    return ranked


def discover_best_phoneshop(
    tool_root: Path | None = None,
    preferred: Path | str | None = None,
) -> PhoneShopLocation | None:
    ranked = discover_phoneshop_locations(tool_root, preferred)
    return ranked[0] if ranked else None


def default_phoneshop_path(
    tool_root: Path | None = None,
    config_path: Path | str | None = None,
) -> tuple[Path | None, str]:
    """Pick path for UI startup. Returns (path, reason)."""
    saved: Path | None = None
    if config_path:
        cfg_file = Path(config_path)
        if cfg_file.is_file():
            import json

            data = json.loads(cfg_file.read_text(encoding="utf-8"))
            raw = (data.get("phoneshop_folder") or "").strip()
            if raw and _is_phoneshop_dir(Path(raw)):
                saved = Path(raw).resolve()

    best = discover_best_phoneshop(tool_root, preferred=saved)
    if best:
        if saved and best.path.resolve() == saved.resolve():
            return best.path, f"Using saved folder ({best.source})"
        return best.path, f"Auto-detected: {best.source}"
    # Fallback: dev path even if lists not created yet
    if tool_root:
        dev = _tool_dev_phoneshop(tool_root)
        if dev:
            return dev, "Default dev path (create buy_list.txt here or Scan+Write)"
    return None, "No Phone Shop folder found — use Browse"
