from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

from .models import ShopEntry, ScannedItem

SHOP_CATEGORIES = [
    "Weapons",
    "Ammo",
    "Weapon ACC",
    "Food",
    "Tools",
    "Medical",
    "Vehicle Parts",
    "Vehicles",
    "Costume",
    "Armor",
    "Clothes",
]

CATEGORY_ORDER = {name: i for i, name in enumerate(SHOP_CATEGORIES)}

_LINE_RE = re.compile(r"^([^|]+)\|([^|]+)\|(\d+)\|([^|]+)$")


def parse_shop_list(path: Path) -> tuple[dict[str, ShopEntry], list[str]]:
    """Return entries (last line wins) and header comment lines."""
    header: list[str] = []
    entries: dict[str, ShopEntry] = {}
    if not path.is_file():
        return entries, header
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            header.append(raw.rstrip())
            continue
        m = _LINE_RE.match(line)
        if not m:
            continue
        item_type, label, price, category = [p.strip() for p in m.groups()]
        entries[item_type] = ShopEntry(item_type, label, int(price), category)
    return entries, header


def sort_key(entry: ShopEntry) -> tuple:
    return (CATEGORY_ORDER.get(entry.category, 99), entry.label.lower())


def write_shop_list(
    path: Path,
    entries: dict[str, ShopEntry],
    header_lines: list[str] | None = None,
    *,
    backup: bool = True,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if backup and path.is_file():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(path, path.with_suffix(path.suffix + f".bak.{stamp}"))
    lines: list[str] = []
    if header_lines:
        lines.extend(header.rstrip() for header in header_lines)
        lines.append("")
    for item_type in sorted(entries, key=lambda k: sort_key(entries[k])):
        lines.append(entries[item_type].line())
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def sell_from_buy(entry: ShopEntry, ratio: float = 0.2) -> ShopEntry:
    return ShopEntry(
        entry.item_type,
        entry.label,
        max(1, int(entry.price * ratio)),
        entry.category,
    )


def merge_entries(
    base: dict[str, ShopEntry],
    scanned: list[ScannedItem],
    *,
    replace_prefix: str | None = None,
) -> dict[str, ShopEntry]:
    out = dict(base)
    if replace_prefix:
        prefix = replace_prefix if replace_prefix.endswith(".") else replace_prefix + "."
        for key in list(out):
            if key.startswith(prefix):
                del out[key]
    for row in scanned:
        if not row.included:
            continue
        out[row.item_type] = row.to_entry()
    return out


def fingerprint(buy: dict[str, ShopEntry], sell: dict[str, ShopEntry]) -> str:
    buy_sum = sum(e.price for e in buy.values())
    sell_sum = sum(e.price for e in sell.values())
    return f"{len(buy)}:{len(sell)}:{buy_sum + sell_sum}"
