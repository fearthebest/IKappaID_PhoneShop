"""Build full Workshop release shop lists: vanilla + GaelGun + MarzGuns + vehicles + UmaBoid costumes."""

from __future__ import annotations

import importlib.util
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSHOP_PHONESHOP = Path(
    r"c:\Users\mpass\Zomboid\Workshop\IKappaID_PhoneShop"
    r"\Contents\mods\IKappaID_PhoneShop\42\media\phoneshop"
)
DEV_PHONESHOP = Path(
    r"c:\Users\mpass\Desktop\PhoneShop_Workshop\PhoneShop_Workshop"
    r"\Contents\mods\IKappaID_PhoneShop\42\media\phoneshop"
)
STEAM_PHONESHOP = Path(
    r"B:\SteamLibrary\steamapps\workshop\content\108600\3749926419"
    r"\mods\IKappaID_PhoneShop\42\media\phoneshop"
)
PRESETS = Path(__file__).resolve().parent.parent / "presets" / "server"
WD = Path(
    r"c:\Users\mpass\Zomboid\Saves\Multiplayer"
    r"\51.91.12.228_27955_afa501309923e3c18593c489e5c852ea\WorldDictionaryReadable.lua"
)

GAEL_MOD_ID = "GaelGunStore_B42"


def load_builder(name: str):
    path = ROOT / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_gaelgun_from_dictionary(server_mod) -> dict[str, tuple[str, int, str]]:
    items: dict[str, tuple[str, int, str]] = {}
    if not WD.is_file():
        print(f"WARN: WorldDictionary missing: {WD}")
        return items
    text = WD.read_text(encoding="utf-8", errors="replace")
    entries = re.findall(r'fulltype = "([^"]+)".*?modID = "([^"]+)"', text, re.S)
    for fulltype, mod_id in entries:
        if mod_id != GAEL_MOD_ID:
            continue
        module, _, name = fulltype.partition(".")
        if module != "Base":
            continue
        cat = server_mod.categorize(fulltype, mod_id)
        if not cat:
            continue
        items[fulltype] = (
            server_mod.label_from_type(fulltype),
            server_mod.default_price(cat, fulltype),
            cat,
        )
    return items


def main() -> None:
    server_mod = load_builder("build_server_shop_lists.py")
    marz_mod = load_builder("build_marz_shop_lists.py")

    buy: dict[str, tuple[str, int, str]] = {}
    for src in (server_mod.USER_BUY, ROOT / "data" / "workshop_vanilla_extra.txt"):
        buy.update(server_mod.parse_list(src))

    gael = load_gaelgun_from_dictionary(server_mod)
    display = marz_mod.load_display_names()
    marz = marz_mod.collect_marz_items(display)

    buy.update(gael)
    buy.update(marz)

    sell_extras = server_mod.parse_list(server_mod.USER_SELL_EXTRAS)
    sell: dict[str, tuple[str, int, str]] = {}
    for item, (label, price, cat) in buy.items():
        sell[item] = (label, max(1, int(price * 0.2)), cat)
    for item, row in sell_extras.items():
        if item not in buy:
            sell[item] = row

    buy_header = (
        "# IKappaID Phone Shop — buy list\n"
        "# Includes vanilla Base.*, GaelGun (GaelGunStore_B42), and MarzGuns items.\n"
        "# Items from mods you do not run are hidden automatically — no extra mods required."
    )
    sell_header = (
        "# IKappaID Phone Shop — sell list (~20% buy + jewelry sell-only)\n"
        "# Same mod notes as buy_list.txt"
    )

    for dest in (WORKSHOP_PHONESHOP, DEV_PHONESHOP):
        dest.mkdir(parents=True, exist_ok=True)
        server_mod.write_list(dest / "buy_list.txt", buy, buy_header)
        server_mod.write_list(dest / "sell_list.txt", sell, sell_header)

        for name in ("vehicle_list.txt", "costume_list.txt"):
            src = PRESETS / name
            if src.is_file():
                shutil.copy2(src, dest / name)
            elif name == "vehicle_list.txt":
                shutil.copy2(WORKSHOP_PHONESHOP / "vehicle_list.txt", dest / name)

    if STEAM_PHONESHOP.parent.parent.exists():
        STEAM_PHONESHOP.mkdir(parents=True, exist_ok=True)
        for name in ("buy_list.txt", "sell_list.txt", "vehicle_list.txt", "costume_list.txt"):
            shutil.copy2(WORKSHOP_PHONESHOP / name, STEAM_PHONESHOP / name)

    mod_counts: dict[str, int] = defaultdict(int)
    for ft in buy:
        mod_counts[ft.split(".", 1)[0]] += 1

    v_lines = sum(1 for _ in open(WORKSHOP_PHONESHOP / "vehicle_list.txt", encoding="utf-8") if re.match(r"^Base\.", _))
    c_lines = sum(1 for _ in open(WORKSHOP_PHONESHOP / "costume_list.txt", encoding="utf-8") if re.match(r"^Base\.", _))

    print(f"Buy: {len(buy)} (GaelGun Base.*: {len(gael)}, MarzGuns: {len(marz)}, vanilla+other: {len(buy)-len(gael)-len(marz)})")
    print(f"Sell: {len(sell)}")
    print(f"vehicle_list.txt lines: {v_lines}")
    print(f"costume_list.txt lines: {c_lines}")
    print("Top prefixes:", dict(sorted(mod_counts.items(), key=lambda x: (-x[1], x[0]))[:8]))
    print(f"Wrote -> {WORKSHOP_PHONESHOP}")


if __name__ == "__main__":
    main()
