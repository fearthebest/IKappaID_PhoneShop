"""Preview stats before merging scanned items into shop lists."""

from __future__ import annotations

from dataclasses import dataclass

from .lists import fingerprint, merge_entries, sell_from_buy
from .models import ShopEntry, ScannedItem


@dataclass
class MergePreview:
    prefix: str
    included_count: int
    buy_added: int
    buy_updated: int
    buy_removed: int
    buy_before: int
    buy_after: int
    sell_touched: int
    sell_after: int
    fp_before: str
    fp_after: str
    samples_added: list[str]
    samples_updated: list[str]
    samples_removed: list[str]


def _prefix_key(prefix: str) -> str:
    return "Base." if prefix == "Base" else prefix + "."


def _entry_changed(a: ShopEntry, b: ShopEntry) -> bool:
    return a.label != b.label or a.price != b.price or a.category != b.category


def preview_merge(
    buy_existing: dict[str, ShopEntry],
    sell_existing: dict[str, ShopEntry],
    scanned: list[ScannedItem],
    *,
    prefix: str,
    sell_ratio: float,
) -> tuple[dict[str, ShopEntry], dict[str, ShopEntry], MergePreview]:
    included = [r for r in scanned if r.included]
    key_prefix = _prefix_key(prefix)

    old_module_keys = [k for k in buy_existing if k.startswith(key_prefix)]
    buy_merged = merge_entries(buy_existing, scanned, replace_prefix=prefix)

    sell_merged = dict(sell_existing)
    for key in list(sell_merged):
        if key.startswith(key_prefix):
            del sell_merged[key]
    for row in included:
        sell_merged[row.item_type] = sell_from_buy(row.to_entry(), sell_ratio)

    new_keys = {r.item_type for r in included}
    added: list[str] = []
    updated: list[str] = []
    for row in included:
        prev = buy_existing.get(row.item_type)
        if not prev:
            added.append(row.item_type)
        elif _entry_changed(prev, row.to_entry()):
            updated.append(row.item_type)
    removed = [k for k in old_module_keys if k not in new_keys]

    preview = MergePreview(
        prefix=prefix,
        included_count=len(included),
        buy_added=len(added),
        buy_updated=len(updated),
        buy_removed=len(removed),
        buy_before=len(buy_existing),
        buy_after=len(buy_merged),
        sell_touched=len(included),
        sell_after=len(sell_merged),
        fp_before=fingerprint(buy_existing, sell_existing),
        fp_after=fingerprint(buy_merged, sell_merged),
        samples_added=added[:8],
        samples_updated=updated[:8],
        samples_removed=removed[:8],
    )
    return buy_merged, sell_merged, preview


def format_preview_text(p: MergePreview, shop: str) -> str:
    lines = [
        f"Target: {shop}",
        f"Module prefix: {p.prefix}",
        f"Included items: {p.included_count}",
        "",
        "BUY list",
        f"  Before: {p.buy_before} lines",
        f"  After:  {p.buy_after} lines",
        f"  +{p.buy_added} new, ~{p.buy_updated} updated, -{p.buy_removed} removed (this module)",
        "",
        "SELL list",
        f"  After: {p.sell_after} lines ({p.sell_touched} module lines refreshed)",
        "",
        f"Fingerprint: {p.fp_before}  →  {p.fp_after}",
    ]
    if p.samples_added:
        lines += ["", "New (sample):", *[f"  + {x}" for x in p.samples_added]]
    if p.samples_updated:
        lines += ["", "Updated (sample):", *[f"  ~ {x}" for x in p.samples_updated]]
    if p.samples_removed:
        lines += ["", "Removed (sample):", *[f"  - {x}" for x in p.samples_removed]]
    return "\n".join(lines)
