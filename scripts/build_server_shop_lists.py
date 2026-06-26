"""Build curated server shop lists from mod load order + WorldDictionary."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

WD = Path(
    r"c:\Users\mpass\Zomboid\Saves\Multiplayer"
    r"\51.91.12.228_27955_afa501309923e3c18593c489e5c852ea\WorldDictionaryReadable.lua"
)
USER_BUY = Path(__file__).resolve().parent / "data" / "user_buy_core.txt"
USER_SELL_EXTRAS = Path(__file__).resolve().parent / "data" / "user_sell_extras.txt"
OUT_BUY = Path(
    r"c:\Users\mpass\Desktop\PhoneShop_Workshop\PhoneShop_Workshop"
    r"\Contents\mods\IKappaID_PhoneShop\42\media\phoneshop\buy_list.txt"
)
OUT_SELL = Path(
    r"c:\Users\mpass\Desktop\PhoneShop_Workshop\PhoneShop_Workshop"
    r"\Contents\mods\IKappaID_PhoneShop\42\media\phoneshop\sell_list.txt"
)
WORKSHOP_DIR = Path(
    r"c:\Users\mpass\Zomboid\Workshop\IKappaID_PhoneShop"
    r"\Contents\mods\IKappaID_PhoneShop\42\media\phoneshop"
)
STEAM_MOD_DIR = Path(
    r"B:\SteamLibrary\steamapps\workshop\content\108600\3749926419"
    r"\mods\IKappaID_PhoneShop\42\media\phoneshop"
)
DOCS_DIR = Path(r"c:\Users\mpass\Downloads\ABDM\Documents")

CATEGORIES = [
    "Weapons",
    "Ammo",
    "Weapon ACC",
    "Food",
    "Tools",
    "Medical",
    "Vehicle Parts",
    "Armor",
    "Clothes",
]

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

GUN_SKIP = re.compile(
    r"(?i)(bowl|feeder|repairbox|camo$|universalrepair|comicbicpen|chairleg|"
    r"casing|repairpack|tempnilitem|placeholder)",
)

GAEL_TOOLS = re.compile(r"(?i)(guncleaningtools|guntoolskit|gunattparts)")

GAEL_OPTIC = re.compile(r"(?i)^\d+p\d|^\d+p[nk]|^pso|^eotech|^acog|^okp|^trijicon|^aimpoint")

GAEL_ACC = re.compile(
    r"(?i)(scope|sight|suppressor|silencer|_stock$|^stock_|handguard|grip|"
    r"laser|flashlight|torch|surefire|gunlight|weaponlight|"
    r"rail|optic|zenit|compensator|muzzle|foregrip|beam|kobra|"
    r"reflex|_hg_|bipod|anpeq|magpul|holster|mount|adapter|brake|choke|"
    r"recoil|buffer|m_lok|ris_|furnitur|furniture|peq|"
    r"vertical|angled|tactical|canister|sheath)",
)


def is_gaelgun_ammo(name: str) -> bool:
    low = name.lower()
    if (
        "shells" in low or "bullets" in low or low.endswith("rounds")
    ) and "box" not in low and "carton" not in low:
        return True
    if low.startswith("clip_"):
        return True
    if re.search(r"(?i)clip\d|\d+clip$|mmclip|_clip\d", low):
        return True
    if low.endswith("clip") and re.search(r"\d", low):
        return True
    if re.search(r"(?i)box\d+", low):
        return True
    if (
        "magazine" in low
        or "drum" in low
        or "carton" in low
        or low.endswith("box")
        or "arrow_" in low
        or low.startswith("bolt_")
        or re.search(r"\d{2,3}(box|bullets|round)", low)
    ):
        return True
    return False


def categorize_gaelgun_base(name: str) -> str | None:
    """GaelGun uses Base.* for guns named AK47, MP5, etc. — default to weapon."""
    if GAEL_TOOLS.search(name):
        return "Tools"
    if GUN_SKIP.search(name):
        return None
    if is_gaelgun_ammo(name):
        return "Ammo"
    if GAEL_OPTIC.search(name) or GAEL_ACC.search(name):
        return "Weapon ACC"
    return "Weapons"


def categorize_scp(name: str, module: str) -> str | None:
    low = name.lower()
    if any(x in low for x in ("injector", "syringe", "hemovita", "emptyinjector")):
        return "Medical"
    if any(x in low for x in ("_mag", "magazine")) or (
        "clip" in low and "machete" not in low
    ):
        return "Ammo"
    if any(x in low for x in ("machete", "p90", "rifle", "pistol", "gun")):
        return "Weapons"
    if "tshirt" in low or "boilersuit" in low:
        return "Clothes"
    if "bag" in low:
        return "Clothes"
    if any(
        x in low
        for x in (
            "hazmat",
            "vest",
            "helmet",
            "armor",
            "mask",
            "goggles",
            "gloves",
            "kneepad",
            "elbow",
            "balaclava",
        )
    ):
        return "Armor"
    if module == "SCP":
        return "Clothes"
    return None


def categorize_undead_survivor(name: str, module: str) -> str | None:
    low = name.lower()
    if module == "Base":
        if "rifle" in low:
            return "Weapons"
        if "scope" in low:
            return "Weapon ACC"
        return None
    if module != "UndeadSurvivor":
        return None
    if any(x in low for x in ("mask", "filter", "bandage")):
        return "Medical"
    if any(x in low for x in ("vest", "helmet", "armor", "mantle")):
        return "Armor"
    if any(x in low for x in ("knife", "machete", "sword", "rifle")):
        return "Weapons"
    if "scope" in low:
        return "Weapon ACC"
    return "Clothes"

LINE_RE = re.compile(r"^([^|]+)\|([^|]+)\|(\d+)\|([^|]+)$")


def categorize(fulltype: str, mod_id: str) -> str | None:
    module, _, name = fulltype.partition(".")
    low = name.lower()

    if mod_id == "herbalist":
        return "Medical"

    if mod_id == "phuncure2":
        return "Medical"

    if mod_id == "AiORepairKit":
        return "Tools"

    if mod_id == "BabyAnimalFood":
        if "feedfor" in low or "claybowl" in low:
            return None
        return "Food"

    if mod_id == "UndeadSurvivor42":
        return categorize_undead_survivor(name, module)

    if mod_id == "H_E_C_U" and module == "D_HECU":
        if "gas" in low or "filter" in low:
            return "Medical"
        if any(x in low for x in ("vest", "armor", "helmet", "goggles")):
            return "Armor"
        return "Clothes"

    if mod_id in {"LBB42", "LDB42", "LCB42", "LFB42", "LKB42", "LNB42", "LSB42", "LTWB42"}:
        if module in {"LB", "LD", "LC", "LF", "LK", "LN", "LS", "LTW"}:
            if any(x in low for x in ("katana", "wakizashi", "naginata", "sword", "axe", "machete")):
                return "Weapons"
            return "Clothes"

    if mod_id == "MedievalZ" and module == "MZ":
        if any(
            x in low
            for x in (
                "sword",
                "axe",
                "mace",
                "spear",
                "bow",
                "crossbow",
                "dagger",
                "hammer",
                "flail",
                "halberd",
            )
        ):
            return "Weapons"
        if any(
            x in low
            for x in (
                "helmet",
                "armor",
                "cuirass",
                "gauntlet",
                "shield",
                "greaves",
                "pauldron",
            )
        ):
            return "Armor"
        return "Clothes"

    if mod_id == "odz_fallout_riotarmorpack":
        if module == "RiotArmorPack":
            return "Armor"
        if module == "Base" and "digest" in low:
            return "Tools"
        return None

    if mod_id == "SCP_Foundation_Pack":
        return categorize_scp(name, module)

    if mod_id == "Cj42Bicscalibur":
        return "Weapons"

    if mod_id in {"GaelGunStore_B42", "Xixi's Weapon Pack"} and module == "Base":
        if "universalrepair" in low:
            return "Tools"
        return categorize_gaelgun_base(name)

    return None


def default_price(category: str, fulltype: str) -> int:
    low = fulltype.lower()
    if category == "Weapons":
        if any(x in low for x in ("launcher", "m79", "grenade", "minigun", "mg131", "m240")):
            return 6000
        if any(x in low for x in ("rifle", "shotgun", "sniper", "carbine")):
            return 1600
        if any(x in low for x in ("pistol", "revolver", "smg", "mp5", "ak47", "ak74", "ak")):
            return 1200
        if any(x in low for x in ("katana", "sword", "claymore", "excalibur")):
            return 2500
        return 800
    if category == "Ammo":
        if "40mm" in low or "he" in low:
            return 600
        if "drum" in low or "magazine" in low or "clip_" in low:
            return 180
        return 80
    if category == "Weapon ACC":
        if "launcher" in low or "m203" in low:
            return 6000
        return 200
    if category == "Food":
        return 50
    if category == "Tools":
        return 150
    if category == "Medical":
        if "mask" in low:
            return 200
        return 80
    if category == "Armor":
        return 900
    if category == "Clothes":
        if "legendary" in low or "bag" in low or "backpack" in low:
            return 450
        return 180
    return 50


def label_from_type(fulltype: str) -> str:
    name = fulltype.split(".", 1)[-1]
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    return name.replace("_", " ")[:52]


def parse_list(path: Path) -> dict[str, tuple[str, int, str]]:
    out: dict[str, tuple[str, int, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = LINE_RE.match(s)
        if not m:
            continue
        item = m.group(1).strip()
        if " " in item or ". " in item:
            continue
        mod = item.split(".", 1)[0]
        if mod in {"MarzGuns", "BagUpgradePlus"}:
            continue
        out[item] = (m.group(2).strip(), int(m.group(3)), m.group(4).strip())
    return out


def load_dictionary() -> list[tuple[str, str]]:
    text = WD.read_text(encoding="utf-8", errors="replace")
    return re.findall(r'fulltype = "([^"]+)".*?modID = "([^"]+)"', text, re.S)


def write_list(path: Path, items: dict[str, tuple[str, int, str]], header: str) -> None:
    by_cat: dict[str, list[tuple[str, str, int, str]]] = defaultdict(list)
    for item, (label, price, cat) in items.items():
        by_cat[cat].append((item, label, price, cat))

    lines = [header, ""]
    for cat in CATEGORIES:
        rows = sorted(by_cat.get(cat, []), key=lambda r: r[0])
        if not rows:
            continue
        lines.append(f"# --- {cat} ---")
        for item, label, price, _ in rows:
            lines.append(f"{item}|{label}|{price}|{cat}")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    buy = parse_list(USER_BUY)
    sell_extras = parse_list(USER_SELL_EXTRAS)

    added = 0
    for fulltype, mod_id in load_dictionary():
        if mod_id not in SHOP_MOD_IDS:
            continue
        if fulltype in buy:
            continue
        cat = categorize(fulltype, mod_id)
        if not cat:
            continue
        buy[fulltype] = (label_from_type(fulltype), default_price(cat, fulltype), cat)
        added += 1

    sell: dict[str, tuple[str, int, str]] = {}
    for item, (label, price, cat) in buy.items():
        sell[item] = (label, max(1, int(price * 0.2)), cat)

    for item, row in sell_extras.items():
        if item not in buy:
            sell[item] = row

    write_list(
        OUT_BUY,
        buy,
        "# IKappaID Phone Shop — buy list (Base staples + server mods; no MarzGuns/VFX dump)",
    )
    write_list(
        OUT_SELL,
        sell,
        "# IKappaID Phone Shop — sell list (~20% buy + pawn/jewelry sell-only)",
    )

    for dest in (WORKSHOP_DIR, DOCS_DIR, STEAM_MOD_DIR):
        dest.mkdir(parents=True, exist_ok=True)
        for name, src in (("buy_list.txt", OUT_BUY), ("sell_list.txt", OUT_SELL)):
            (dest / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    by_cat: dict[str, int] = defaultdict(int)
    for _, _, cat in buy.values():
        by_cat[cat] += 1

    mod_counts: dict[str, int] = defaultdict(int)
    for ft in buy:
        mod_counts[ft.split(".", 1)[0]] += 1

    print(f"Buy items: {len(buy)} (your Base staples: {len(buy) - added}, from server mods: {added})")
    print(f"Sell items: {len(sell)}")
    print("Buy by category:", dict(sorted(by_cat.items())))
    print("Top module prefixes:")
    for mod, n in sorted(mod_counts.items(), key=lambda x: (-x[1], x[0]))[:12]:
        print(f"  {mod}: {n}")


if __name__ == "__main__":
    main()
