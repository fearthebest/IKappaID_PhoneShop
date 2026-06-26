"""Audit shop list builder: missing items and miscategorization per mod."""

from __future__ import annotations

import importlib.util
import re
from collections import defaultdict
from pathlib import Path

WD = Path(
    r"c:\Users\mpass\Zomboid\Saves\Multiplayer"
    r"\51.91.12.228_27955_afa501309923e3c18593c489e5c852ea\WorldDictionaryReadable.lua"
)
BUY = Path(
    r"c:\Users\mpass\Zomboid\Workshop\IKappaID_PhoneShop"
    r"\Contents\mods\IKappaID_PhoneShop\42\media\phoneshop\buy_list.txt"
)
BUILD = Path(__file__).resolve().parent / "build_server_shop_lists.py"

SHOP_MOD_IDS = {
    "GaelGunStore_B42",
    "H_E_C_U",
    "LBB42",
    "LDB42",
    "LCB42",
    "LFB42",
    "LKB42",
    "LNB42",
    "LSB42",
    "LTWB42",
    "MedievalZ",
    "odz_fallout_riotarmorpack",
    "SCP_Foundation_Pack",
    "UndeadSurvivor42",
    "AiORepairKit",
    "Xixi's Weapon Pack",
    "phuncure2",
    "herbalist",
    "BabyAnimalFood",
    "Cj42Bicscalibur",
}


def load_builder():
    spec = importlib.util.spec_from_file_location("builder", BUILD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    builder = load_builder()
    text = WD.read_text(encoding="utf-8", errors="replace")
    entries = re.findall(r'fulltype = "([^"]+)".*?modID = "([^"]+)"', text, re.S)

    buy: dict[str, str] = {}
    for line in BUY.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([^|]+)\|[^|]+\|\d+\|([^|]+)$", line.strip())
        if m:
            buy[m.group(1)] = m.group(2)

    by_mod: dict[str, list[str]] = defaultdict(list)
    for ft, mid in entries:
        if mid in SHOP_MOD_IDS:
            by_mod[mid].append(ft)

    print("=== Base.* items on non-GaelGun mods (module mismatch) ===")
    for mid in sorted(SHOP_MOD_IDS):
        if mid in {"GaelGunStore_B42", "Xixi's Weapon Pack"}:
            continue
        base_items = [ft for ft in by_mod.get(mid, []) if ft.startswith("Base.")]
        if base_items:
            missing = [ft for ft in base_items if ft not in buy]
            print(f"{mid}: {len(base_items)} Base.* ({len(missing)} not in buy)")
            for ft in sorted(missing)[:10]:
                print(f"  {ft} -> categorize={builder.categorize(ft, mid)}")

    print("\n=== Missing from buy list (categorize returned None) ===")
    missing_total = 0
    for mid in sorted(SHOP_MOD_IDS):
        missing = []
        for ft in by_mod.get(mid, []):
            if ft in buy:
                continue
            cat = builder.categorize(ft, mid)
            if cat is None:
                missing.append(ft)
        if missing:
            missing_total += len(missing)
            print(f"\n{mid}: {len(missing)} missing / {len(by_mod[mid])} in WorldDictionary")
            for ft in sorted(missing)[:15]:
                print(f"  {ft}")
            if len(missing) > 15:
                print(f"  ... +{len(missing) - 15} more")

    print(f"\nTotal missing (skipped by rules): {missing_total}")

    print("\n=== In WD + categorized but not in buy (should be 0) ===")
    gap = 0
    for ft, mid in entries:
        if mid not in SHOP_MOD_IDS or ft in buy:
            continue
        cat = builder.categorize(ft, mid)
        if cat:
            gap += 1
            if gap <= 20:
                print(f"  {ft} -> {cat} ({mid})")
    print(f"Gap count: {gap}")

    print("\n=== Likely miscategorized (name vs category) ===")
    misc = []
    checks = [
        (re.compile(r"(?i)shells|bullets|clip_|magazine|_box$|carton"), "Ammo", "Weapons"),
        (re.compile(r"(?i)scope|sight|suppressor|_stock$|handguard|bipod"), "Weapon ACC", "Weapons"),
        (re.compile(r"(?i)sword|rifle|pistol|shotgun|ak47|mp5|katana|machete"), "Weapons", "Ammo"),
        (re.compile(r"(?i)backpack|bag_|duffel|schoolbag"), "Clothes", "Weapons"),
        (re.compile(r"(?i)helmet|armor|vest|cuirass|shield"), "Armor", "Clothes"),
        (re.compile(r"(?i)mask|syringe|bandage|pill|medical"), "Medical", "Clothes"),
    ]
    for ft, cat in buy.items():
        name = ft.split(".", 1)[-1]
        for pat, good, bad in checks:
            if pat.search(name) and cat == bad:
                misc.append((ft, cat, f"expected {good}"))
                break
    for row in misc[:40]:
        print(f"  {row[0]} | {row[1]} | {row[2]}")
    print(f"Miscategorized sample count: {len(misc)}")

    print("\n=== GaelGun spot checks ===")
    for name in (
        "AK47",
        "AK74",
        "MP5",
        "G3",
        "Mosin",
        "M79",
        "AA12",
        "Clip_AK47",
        "AK47_stock",
        "box_rifle_casing",
        "9mmClip",
    ):
        ft = f"Base.{name}"
        cat = builder.categorize_gaelgun_base(name)
        in_buy = ft in buy
        print(f"  {ft}: cat={cat} in_buy={in_buy} buy_cat={buy.get(ft)}")


if __name__ == "__main__":
    main()
