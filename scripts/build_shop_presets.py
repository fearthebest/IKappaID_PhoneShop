"""Build Phone Shop preset list files from server mod load order."""

from __future__ import annotations

import re
from pathlib import Path

MOD_EXPORT = Path(
    r"C:\Users\mpass\Zomboid\Lua\ModLoadOrder_Exports"
    r"\ModLoadOrder_Export_20260622_211622.txt"
)
UMABOID_ITEMS = Path(
    r"C:\Users\mpass\Zomboid\Workshop\UmaBoidB42"
    r"\Contents\mods\UmaBoidB42\42\media\scripts\UmaBoidItems.txt"
)
OUT_DIR = Path(__file__).resolve().parent.parent / "presets" / "server"

WORKSHOP_ROOTS = [
    Path(r"B:\SteamLibrary\steamapps\workshop\content\108600"),
    Path(r"C:\Users\mpass\Zomboid\Workshop"),
]

# Vehicle packs from ModLoadOrder (damnlib .. rSemiTruck), excluding libraries/patches.
VEHICLE_MOD_IDS = [
    "04vwTouran", "49powerWagon", "59meteor", "63beetle", "63Type2Van", "65banshee",
    "66pontiacLeMans", "67commando", "67gt500", "68firebird", "69camaro", "69charger",
    "69mini", "69mini_PitbullSpecial", "70barracuda", "70dodge", "70fordEscort",
    "70roadRunner", "73fordFalcon", "73fordFalconPS", "75grandPrix", "76chevyKseries",
    "76chryslerNewYorker", "77firebird", "78amgeneralM35A2", "78lamboCountach",
    "79camaro", "80manKat1", "81deloreanDMC12", "81deloreanDMC12BTTF", "82firebird",
    "82firebirdKITT", "82jeepJ10", "82porsche911", "83amgeneralM923", "84buickElectra",
    "84cadillacDeVille", "84corvette", "84jeepXJ", "84merc", "84oldsmobile98",
    "85buickLeSabre", "85chevyCaprice", "85chevyStepVan", "85chevyStepVanexpanded",
    "85oldsmobileDelta88", "85pontiacParisienne", "86chevyCUCV", "86fordE150",
    "86fordE150expanded", "86fordE150mm", "86oshkoshP19A", "87buickRegal",
    "87chevySuburban", "87fordB700", "87toyotaMR2", "88chevyS10", "88toyotaHilux",
    "89defender", "89dodgeCaravan", "89fordBronco", "89trooper", "89volvo200",
    "90bmwE30", "90fordF350ambulance", "90pierceArrow", "91fordLTD", "91fordRanger",
    "91geoMetro", "91nissan240sx", "91range", "92amgeneralM998", "92fordCVPI",
    "92jeepYJ", "92nissanGTR", "93chevySuburban", "93chevySuburbanExpanded",
    "93fordF350", "93fordTaurus", "93mustangSSP", "93townCar", "95impreza",
    "96lancerEVO", "96saturnSseries", "97bushmaster", "98stagea", "99fordCVPI",
    "tsarslib", "ATA_Luton_B42", "ATA_Mustang", "ATA_Mustang_66",
    "ATA_Petyarbuilt", "autotsartrailers", "CytU1550L", "DumpTruckGravelMod",
    "ECTO1", "fhqMotoriousZone", "isoContainers", "KI5campers", "KI5trailers",
    "rSemiTruck",
]

VANILLA_VEHICLES = [
    ("Base.SmallCar", "Small Car", 6000),
    ("Base.CarNormal", "Standard Car", 8000),
    ("Base.CarStationWagon", "Station Wagon", 8500),
    ("Base.OffRoad", "Off-Road", 10000),
    ("Base.PickUpTruck", "Pickup Truck", 10000),
    ("Base.PickUpVan", "Van", 9000),
    ("Base.SUV", "SUV", 12000),
    ("Base.CarLightsPolice", "Police Cruiser", 15000),
    ("Base.PickUpVanLightsPolice", "Police Van", 14000),
    ("Base.ModernCar", "Modern Car", 11000),
    ("Base.CarLuxury", "Luxury Car", 14000),
    ("Base.SportsCar", "Sports Car", 16000),
]

SKIP_VEHICLE_NAME = re.compile(
    r"(?i)trailer|smashed|burnt|wreck|template|placeholder|hidden",
)
SKIP_VEHICLE_FILE = re.compile(r"(?i)template_|_template|models|fixing|items|recipe|dismantle")

MODULE_RE = re.compile(r"^\s*module\s+(\S+)")
VEHICLE_RE = re.compile(r"^\s*vehicle\s+(\S+)")

COSTUME_SKIP = re.compile(
    r"(?i)casual|alt|glasses|ribbon|bag|scarf|crown|hat|veil|tiara|hair|"
    r"umbrella|staff|broom|mallet|bomb|weapon|naginata|sword|shinai|"
    r"claymore|golf|needle|target|fx|anime",
)


def find_mod_dirs(mod_id: str) -> list[Path]:
    found: list[Path] = []
    for root in WORKSHOP_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob(f"mods/{mod_id}"):
            if p.name != mod_id:
                continue
            if (p / "media").is_dir() or any(p.glob("42*/media")):
                found.append(p)
    return list(dict.fromkeys(found))


def vehicle_script_files(mod_dir: Path) -> list[Path]:
    out: list[Path] = []
    for pattern in ("media/scripts/vehicles/*.txt", "42*/media/scripts/vehicles/*.txt"):
        for f in mod_dir.glob(pattern):
            if SKIP_VEHICLE_FILE.search(f.name):
                continue
            out.append(f)
    return sorted(set(out))


def parse_vehicles_from_file(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    module = "Base"
    rows: list[tuple[str, str]] = []
    for line in text.splitlines():
        mm = MODULE_RE.match(line)
        if mm:
            module = mm.group(1)
            continue
        vm = VEHICLE_RE.match(line)
        if not vm:
            continue
        name = vm.group(1)
        if SKIP_VEHICLE_NAME.search(name):
            continue
        full = f"{module}.{name}"
        label = re.sub(r"([a-z])([A-Z0-9])", r"\1 \2", name)
        label = re.sub(r"([A-Za-z])(\d)", r"\1 \2", label)
        rows.append((full, label.strip()))
    return rows


def price_for_vehicle(full: str, name: str) -> int:
    low = (full + name).lower()
    if any(x in low for x in ("lambo", "delorean", "gtr", "corvette", "porsche", "countach")):
        return 45000
    if any(x in low for x in ("m35", "m923", "m998", "bushmaster", "oshkosh", "kat", "semi", "dump")):
        return 32000
    if any(x in low for x in ("ambulance", "fire", "police", "cvpi", "ssp", "pierce")):
        return 28000
    if any(x in low for x in ("trailer", "camper", "luton", "container")):
        return 12000
    if name.startswith("Base."):
        return 10000
    return 24000


def collect_server_vehicles() -> list[tuple[str, str, int, int]]:
    seen: set[str] = set()
    rows: list[tuple[str, str, int, int]] = []

    for full, label, price in VANILLA_VEHICLES:
        if full not in seen:
            seen.add(full)
            rows.append((full, label, price, 1))

    for mod_id in VEHICLE_MOD_IDS:
        for mod_dir in find_mod_dirs(mod_id):
            for vfile in vehicle_script_files(mod_dir):
                for full, label in parse_vehicles_from_file(vfile):
                    if full in seen:
                        continue
                    seen.add(full)
                    price = price_for_vehicle(full, label)
                    rows.append((full, label, price, 1))

    rows.sort(key=lambda r: (r[0].split(".", 1)[0], r[1].lower()))
    return rows


def collect_umaboid_costumes() -> list[tuple[str, str, int]]:
    if not UMABOID_ITEMS.exists():
        return []
    seen: set[str] = set()
    rows: list[tuple[str, str, int]] = []
    for line in UMABOID_ITEMS.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^\s*item\s+(\w+)", line)
        if not m:
            continue
        name = m.group(1)
        if COSTUME_SKIP.search(name):
            continue
        full = f"Base.{name}"
        if full in seen:
            continue
        seen.add(full)
        label = re.sub(r"([a-z])([A-Z0-9])", r"\1 \2", name)
        price = 3500 if "Wedding" not in name else 4000
        rows.append((full, label.strip(), price))
    rows.sort(key=lambda r: r[1].lower())
    return rows


def write_vehicle_list(path: Path, rows: list[tuple[str, str, int, int]]) -> None:
    lines = [
        "# IKappaID Phone Shop — SERVER preset (vehicle_list.txt)",
        "# Upload via FileZilla to:",
        "#   Contents/mods/IKappaID_PhoneShop/42/media/phoneshop/vehicle_list.txt",
        "# Requires IKappaIDPinkSlip + vehicle mods on server and clients.",
        "# Format: vehicleScript|label|price|hasKey(0|1)",
        "# Generated from ModLoadOrder_Export_20260622_211622.txt",
        "",
    ]
    for full, label, price, key in rows:
        lines.append(f"{full}|{label}|{price}|{key}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_costume_list(path: Path, rows: list[tuple[str, str, int]]) -> None:
    lines = [
        "# IKappaID Phone Shop — SERVER preset (costume_list.txt)",
        "# Upload via FileZilla to:",
        "#   Contents/mods/IKappaID_PhoneShop/42/media/phoneshop/costume_list.txt",
        "# Requires UmaBoid_B42_Miroki on server and clients.",
        "# Format: itemType|label|price",
        "",
    ]
    for full, label, price in rows:
        lines.append(f"{full}|{label}|{price}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_readme(path: Path, vehicle_count: int, costume_count: int) -> None:
    path.write_text(
        f"""IKappaID Phone Shop — server presets (FileZilla)

Generated for mod loadout: ModLoadOrder_Export_20260622_211622.txt

FILES
  vehicle_list.txt   — {vehicle_count} pink-slip vehicles (vanilla + KI5/ATA/MZ/etc.)
  costume_list.txt   — {costume_count} UmaBoid costumes

UPLOAD TARGET (dedicated server)
  Zomboid/media/mods/IKappaID_PhoneShop/42/media/phoneshop/
  — or your Workshop mirror with the same path under Contents/mods/

After upload:
  1. Restart the dedicated server fully.
  2. Clients need the same files (Workshop re-upload or matching folder).

OPTIONAL local sync:
  Copy into:
    PhoneShop_Workshop\\...\\media\\phoneshop\\
    Zomboid\\Workshop\\IKappaID_PhoneShop\\...\\media\\phoneshop\\
  Then run: scripts\\sync_shop_lists.ps1

NOTES
  - Vehicles only show when that vehicle mod is loaded in the save.
  - Edit prices/labels in the txt files anytime; lines starting with # are ignored.
  - Remove lines you do not want on the server before uploading.
""",
        encoding="utf-8",
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    vehicles = collect_server_vehicles()
    costumes = collect_umaboid_costumes()
    write_vehicle_list(OUT_DIR / "vehicle_list.txt", vehicles)
    write_costume_list(OUT_DIR / "costume_list.txt", costumes)
    write_readme(OUT_DIR / "README_FileZilla.txt", len(vehicles), len(costumes))
    print(f"Wrote {len(vehicles)} vehicles -> {OUT_DIR / 'vehicle_list.txt'}")
    print(f"Wrote {len(costumes)} costumes -> {OUT_DIR / 'costume_list.txt'}")
    print(f"Guide -> {OUT_DIR / 'README_FileZilla.txt'}")


if __name__ == "__main__":
    main()
