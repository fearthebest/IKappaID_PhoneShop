"""Build shop lists for Sandbox save 2026-06-25_21-40-23 — vanilla + Marz + Gael + test vehicles."""

from __future__ import annotations

import importlib.util
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SAVE_WD = Path(
    r"c:\Users\mpass\Zomboid\Saves\Sandbox\2026-06-25_21-40-23\WorldDictionaryReadable.lua"
)
MP_WD = Path(
    r"c:\Users\mpass\Zomboid\Saves\Multiplayer"
    r"\51.91.12.228_27955_afa501309923e3c18593c489e5c852ea\WorldDictionaryReadable.lua"
)
GAEL_MOD_ID = "GaelGunStore_B42"

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
DESKTOP_OUT = Path(r"c:\Users\mpass\Desktop\PhoneShop_lists_2026-06-25_21-40_save")

VEHICLE_LIST = """# IKappaID Phone Shop — TEST save vehicle_list.txt (Sandbox 2026-06-25_21-40)
# Format: vehicleScript|label|price|hasKey(0|1)
# Pink slips — enable IKappaIDPinkSlip + vehicle mods for each entry.

Base.SmallCar|Small Car|5000|1
Base.CarNormal|Standard Car|7500|1
Base.CarStationWagon|Station Wagon|8000|1
Base.OffRoad|Off-Road|9500|1
Base.PickUpTruck|Pickup Truck|9500|1
Base.PickUpVan|Van|8500|1
Base.SUV|SUV|11000|1
Base.ModernCar|Modern Car|10000|1
Base.CarLightsPolice|Police Cruiser|14000|1
Base.PickUpVanLightsPolice|Police Van|13000|1
"""

COSTUME_LIST = """# IKappaID Phone Shop — TEST save costume_list.txt
# Empty for this save (UmaBoid not enabled). Add lines when UmaBoid_B42_Miroki is on.
# Format: itemType|label|price
"""


def load_builder(name: str):
    path = ROOT / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_gaelgun_from_dictionary(wd_path: Path, server_mod) -> dict[str, tuple[str, int, str]]:
    items: dict[str, tuple[str, int, str]] = {}
    if not wd_path.is_file():
        return items
    text = wd_path.read_text(encoding="utf-8", errors="replace")
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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    server_mod = load_builder("build_server_shop_lists.py")
    marz_mod = load_builder("build_marz_shop_lists.py")

    buy: dict[str, tuple[str, int, str]] = {}
    for src in (server_mod.USER_BUY, ROOT / "data" / "workshop_vanilla_extra.txt"):
        buy.update(server_mod.parse_list(src))

    gael = load_gaelgun_from_dictionary(SAVE_WD, server_mod)
    if len(gael) < 50 and MP_WD.is_file():
        gael = load_gaelgun_from_dictionary(MP_WD, server_mod)

    display = marz_mod.load_display_names()
    marz = marz_mod.collect_marz_items(display)

    buy.update(gael)
    buy.update(marz)

    # Obvious test prices on a few staples (easy to spot in-game)
    for test_key, test_price in (
        ("Base.Axe", 99),
        ("Base.Hammer", 49),
        ("MarzGuns.AK47", 1337),
        ("MarzGuns.M4A1", 1500),
    ):
        if test_key in buy:
            label, _, cat = buy[test_key]
            buy[test_key] = (label, test_price, cat)

    sell: dict[str, tuple[str, int, str]] = {}
    for item, (label, price, cat) in buy.items():
        sell[item] = (label, max(1, int(price * 0.2)), cat)
    for item, row in server_mod.parse_list(server_mod.USER_SELL_EXTRAS).items():
        if item not in buy:
            sell[item] = row

    buy_header = (
        "# IKappaID Phone Shop — TEST buy list (Sandbox save 2026-06-25_21-40)\n"
        "# Vanilla + MarzGuns + GaelGun. Hidden if mod not enabled in this save.\n"
        "# TEST PRICES: Axe $99, Hammer $49, Marz AK47 $1337, M4 $1500"
    )
    sell_header = (
        "# IKappaID Phone Shop — TEST sell list (Sandbox save 2026-06-25_21-40)\n"
        "# ~20% of buy + jewelry sell-only extras"
    )

    currency_src = DEV_PHONESHOP / "currency_list.txt"
    if not currency_src.is_file():
        currency_src = WORKSHOP_PHONESHOP / "currency_list.txt"

    dests = (WORKSHOP_PHONESHOP, DEV_PHONESHOP, DESKTOP_OUT)
    for dest in dests:
        dest.mkdir(parents=True, exist_ok=True)
        server_mod.write_list(dest / "buy_list.txt", buy, buy_header)
        server_mod.write_list(dest / "sell_list.txt", sell, sell_header)
        write_text(dest / "vehicle_list.txt", VEHICLE_LIST)
        write_text(dest / "costume_list.txt", COSTUME_LIST)
        if currency_src.is_file():
            try:
                (dest / "currency_list.txt").write_text(
                    currency_src.read_text(encoding="utf-8"), encoding="utf-8"
                )
            except OSError:
                pass

    if STEAM_PHONESHOP.parent.parent.exists():
        STEAM_PHONESHOP.mkdir(parents=True, exist_ok=True)
        for name in ("buy_list.txt", "sell_list.txt", "vehicle_list.txt", "costume_list.txt"):
            try:
                shutil.copy2(WORKSHOP_PHONESHOP / name, STEAM_PHONESHOP / name)
            except OSError:
                pass

    mod_counts: dict[str, int] = defaultdict(int)
    for ft in buy:
        mod_counts[ft.split(".", 1)[0]] += 1

    print(f"Save: {SAVE_WD.parent.name}")
    print(f"Buy: {len(buy)} (GaelGun: {len(gael)}, MarzGuns: {len(marz)}, other: {len(buy)-len(gael)-len(marz)})")
    print(f"Sell: {len(sell)}")
    print(f"Vehicles: 10 test pink slips | Costumes: 0")
    print("Prefixes:", dict(sorted(mod_counts.items(), key=lambda x: (-x[1], x[0]))[:6]))
    print(f"Wrote -> {WORKSHOP_PHONESHOP}")
    print(f"Backup -> {DESKTOP_OUT}")
    print()
    print("NOTE: This save mods.txt has NO MarzGuns/GaelGun/UmaBoid enabled.")
    print("      Enable those mods in the save for gun items to appear in the shop UI.")


if __name__ == "__main__":
    main()
