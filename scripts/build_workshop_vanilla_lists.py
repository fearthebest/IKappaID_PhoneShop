"""Build vanilla buy/sell lists for public Workshop upload."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
USER_BUY = ROOT / "data" / "user_buy_core.txt"
EXTRA = ROOT / "data" / "workshop_vanilla_extra.txt"
SELL_EXTRAS = ROOT / "data" / "user_sell_extras.txt"

WORKSHOP_PHONESHOP = Path(
    r"c:\Users\mpass\Zomboid\Workshop\IKappaID_PhoneShop"
    r"\Contents\mods\IKappaID_PhoneShop\42\media\phoneshop"
)
DEV_PHONESHOP = Path(
    r"c:\Users\mpass\Desktop\PhoneShop_Workshop\PhoneShop_Workshop"
    r"\Contents\mods\IKappaID_PhoneShop\42\media\phoneshop"
)

VEHICLE_LIST = """# IKappaID Phone Shop — Vehicles tab
# Format: vehicleScript|label|price|hasKey(0|1)
# Default: vanilla vehicles. Add or remove lines for your server.

Base.SmallCar|Small Car|6000|1
Base.CarNormal|Standard Car|8000|1
Base.CarStationWagon|Station Wagon|8500|1
Base.OffRoad|Off-Road|10000|1
Base.PickUpTruck|Pickup Truck|10000|1
Base.PickUpVan|Van|9000|1
Base.SUV|SUV|12000|1
Base.CarLightsPolice|Police Cruiser|15000|1
Base.PickUpVanLightsPolice|Police Van|14000|1
Base.ModernCar|Modern Car|11000|1
"""

COSTUME_LIST = """# IKappaID Phone Shop — Costume tab
# Empty by default. Add lines for your server.
# Format: itemType|label|price
"""


def parse_list(path: Path) -> dict[str, tuple[str, int, str]]:
    items: dict[str, tuple[str, int, str]] = {}
    if not path.exists():
        return items
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) != 4:
            continue
        item_type, label, price, category = [p.strip() for p in parts]
        p = int(price)
        items[item_type] = (label, p, category)
    return items


def write_list(path: Path, items: dict[str, tuple[str, int, str]], header: str) -> None:
    lines = [header.rstrip(), ""]
    for item_type in sorted(items, key=lambda k: (items[k][2], items[k][0].lower())):
        label, price, category = items[item_type]
        lines.append(f"{item_type}|{label}|{price}|{category}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    buy: dict[str, tuple[str, int, str]] = {}
    for src in (USER_BUY, EXTRA):
        buy.update(parse_list(src))

    sell: dict[str, tuple[str, int, str]] = {}
    for item, (label, price, cat) in buy.items():
        sell[item] = (label, max(1, int(price * 0.2)), cat)
    for item, row in parse_list(SELL_EXTRAS).items():
        if item not in buy:
            sell[item] = row

    buy_header = (
        "# IKappaID Phone Shop — buy list (vanilla Base.* starter preset)\n"
        "# Add your mod items or replace this file on dedicated servers."
    )
    sell_header = (
        "# IKappaID Phone Shop — sell list (~20% buy + jewelry sell-only)\n"
        "# Add your mod items or replace this file on dedicated servers."
    )

    for dest in (WORKSHOP_PHONESHOP, DEV_PHONESHOP):
        dest.mkdir(parents=True, exist_ok=True)
        write_list(dest / "buy_list.txt", buy, buy_header)
        write_list(dest / "sell_list.txt", sell, sell_header)
        (dest / "vehicle_list.txt").write_text(VEHICLE_LIST, encoding="utf-8")
        (dest / "costume_list.txt").write_text(COSTUME_LIST, encoding="utf-8")

    print(f"Vanilla buy items: {len(buy)}")
    print(f"Vanilla sell items: {len(sell)}")
    print(f"Wrote -> {WORKSHOP_PHONESHOP}")


if __name__ == "__main__":
    main()
