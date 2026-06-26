"""Estimate which buy-list items are hidden in-game (no ScriptManager entry)."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

BUY = Path(
    r"c:\Users\mpass\Zomboid\Workshop\IKappaID_PhoneShop"
    r"\Contents\mods\IKappaID_PhoneShop\42\media\phoneshop\buy_list.txt"
)
WD = Path(
    r"c:\Users\mpass\Zomboid\Saves\Multiplayer"
    r"\51.91.12.228_27955_afa501309923e3c18593c489e5c852ea\WorldDictionaryReadable.lua"
)

# Mod prefix -> modID on server (for grouping hidden items)
PREFIX_HINT = {
    "LB": "LBB42",
    "LD": "LDB42",
    "LC": "LCB42",
    "LF": "LFB42",
    "LK": "LKB42",
    "LN": "LNB42",
    "LS": "LSB42",
    "LTW": "LTWB42",
    "MZ": "MedievalZ",
    "D_HECU": "H_E_C_U",
    "UndeadSurvivor": "UndeadSurvivor42",
    "SCP": "SCP_Foundation_Pack",
    "RiotArmorPack": "odz_fallout_riotarmorpack",
    "Herbalist": "herbalist",
    "PhunCure": "phuncure2",
}


def main() -> None:
    text = WD.read_text(encoding="utf-8", errors="replace")
    wd_types = {
        m.group(1)
        for m in re.finditer(r'fulltype = "([^"]+)"', text)
    }

    items = []
    for line in BUY.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([^|]+)\|([^|]+)\|(\d+)\|([^|]+)$", line.strip())
        if m:
            items.append(m.group(1))

    by_prefix: dict[str, int] = defaultdict(int)
    base_gael_hidden = 0
    base_other = 0
    in_wd_not_guess = []

    for ft in items:
        if ft in wd_types:
            continue
        prefix = ft.split(".", 1)[0]
        by_prefix[prefix] += 1
        if prefix == "Base":
            # GaelGun uses Base.* — if in WD under GaelGun it's "known" when mod loaded
            in_wd_not_guess.append(ft)

    print(f"Buy list items: {len(items)}")
    print(f"Not in WorldDictionary save file: {sum(by_prefix.values())}")
    print("\nHidden by module prefix (not in WD export):")
    for p, n in sorted(by_prefix.items(), key=lambda x: (-x[1], x[0])):
        hint = PREFIX_HINT.get(p, "?")
        print(f"  {p}: {n}  (enable {hint})")

    # Items in list that ARE in WD - when GaelGun loaded, Base.* from GaelGun should show
    # Count non-Base prefixes in buy list
    non_base = [ft for ft in items if not ft.startswith("Base.")]
    print(f"\nNon-Base.* shop lines: {len(non_base)}")
    for p in sorted({ft.split('.')[0] for ft in non_base}):
        n = sum(1 for ft in non_base if ft.startswith(p + "."))
        print(f"  {p}: {n}")


if __name__ == "__main__":
    main()
