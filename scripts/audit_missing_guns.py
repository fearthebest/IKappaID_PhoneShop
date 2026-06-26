"""Find GaelGun weapons missing from buy list due to categorize gaps."""

from __future__ import annotations

import re
from pathlib import Path

WD = Path(
    r"c:\Users\mpass\Zomboid\Saves\Multiplayer"
    r"\51.91.12.228_27955_afa501309923e3c18593c489e5c852ea\WorldDictionaryReadable.lua"
)
BUY = Path(
    r"c:\Users\mpass\Zomboid\Workshop\IKappaID_PhoneShop"
    r"\Contents\mods\IKappaID_PhoneShop\42\media\phoneshop\buy_list.txt"
)

GUN_SKIP = re.compile(
    r"(?i)(bowl|feeder|repairbox|camo$|cleaningtools|toolskit|attparts|"
    r"universalrepair|sheath$|comicbicpen|chairleg)",
)


def categorize_name(name: str) -> str | None:
    low = name.lower()
    if GUN_SKIP.search(name):
        return None
    if (
        "shells" in low or "bullets" in low or low.endswith("rounds")
    ) and "box" not in low and "carton" not in low:
        return "Ammo"
    if (
        low.startswith("clip_")
        or "magazine" in low
        or "drum" in low
        or "carton" in low
        or low.endswith("box")
        or "bullets" in low
        or "arrow_" in low
        or "bolt_" in low
        or re.search(r"\d{2,3}(box|bullets|round)", low)
    ):
        return "Ammo"
    if any(
        x in low
        for x in (
            "scope",
            "sight",
            "suppressor",
            "stock",
            "handguard",
            "grip",
            "laser",
            "light",
            "rail",
            "optic",
            "zenit",
            "compensator",
            "muzzle",
            "foregrip",
            "beam",
            "kobra",
            "reflex",
            "silencer",
        )
    ) or "_hg_" in low or low.endswith("_stock"):
        return "ACC"
    if any(
        x in low
        for x in (
            "rifle",
            "pistol",
            "shotgun",
            "smg",
            "revolver",
            "launcher",
            "minigun",
            "crossbow",
            "bow",
            "katana",
            "machete",
            "sword",
            "knife",
        )
    ) and "box" not in low and "bowl" not in low:
        return "Weapons"
    return None


def main() -> None:
    text = WD.read_text(encoding="utf-8", errors="replace")
    entries = re.findall(r'fulltype = "([^"]+)".*?modID = "([^"]+)"', text, re.S)
    buy = set()
    for line in BUY.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([^|]+)\|", line.strip())
        if m:
            buy.add(m.group(1))

    gg = [
        ft
        for ft, mid in entries
        if mid in {"GaelGunStore_B42", "Xixi's Weapon Pack"} and ft.startswith("Base.")
    ]

    none_cat = []
    for ft in gg:
        name = ft.split(".", 1)[1]
        if categorize_name(name) is None and ft not in buy:
            none_cat.append(ft)

    print(f"GaelGun/Xixi Base.* in WorldDictionary: {len(gg)}")
    print(f"In buy list: {sum(1 for ft in gg if ft in buy)}")
    print(f"Missing (categorize=None): {len(none_cat)}")
    print("Examples:", none_cat[:40])


if __name__ == "__main__":
    main()
