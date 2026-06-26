"""Build Phone Shop buy/sell lists for Guns of Marz (MarzGuns module)."""

from __future__ import annotations

import json
import re
from pathlib import Path

MARZ_ROOTS = [
    Path(
        r"B:\SteamLibrary\steamapps\workshop\content\108600\3722134990"
        r"\mods\GunsOfMarz\42.16\media\scripts\MarzWeapons\items"
    ),
    Path(
        r"c:\Users\mpass\Desktop\3722134990\mods\GunsOfMarz"
        r"\42.16\media\scripts\MarzWeapons\items"
    ),
]
ITEM_NAMES = [
    Path(
        r"B:\SteamLibrary\steamapps\workshop\content\108600\3722134990"
        r"\mods\GunsOfMarz\42.16\media\lua\shared\Translate\EN\ItemName.json"
    ),
]
VANILLA_BUY = Path(__file__).resolve().parent / "data" / "user_buy_core.txt"
VANILLA_EXTRA = Path(__file__).resolve().parent / "data" / "workshop_vanilla_extra.txt"
OUT_DIR = Path(r"c:\Users\mpass\Desktop\IKappaID_PhoneShop_MarzGuns_lists")

MODULE = "MarzGuns"
ITEM_RE = re.compile(r"^\s*item\s+(\S+)")

SKIP_NAMES = re.compile(
    r"(?i)^(FakeItem|Bullet_\d+|40mm_HE_Explosion)$",
)
SKIP_PATH = re.compile(
    r"(?i)([/\\]fx[/\\]|[/\\]spawners[/\\]|[/\\]generic\.txt$|ammo_casings\.txt$)",
)


def resolve_marz_root() -> Path:
    for root in MARZ_ROOTS:
        if root.is_dir():
            return root
    raise FileNotFoundError("GunsOfMarz items folder not found")


def load_display_names() -> dict[str, str]:
    for path in ITEM_NAMES:
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        return {str(k): str(v) for k, v in data.items() if k.startswith("MarzGuns.")}
    return {}


def label_from_name(name: str, display: dict[str, str]) -> str:
    full = f"{MODULE}.{name}"
    if full in display and display[full].strip():
        return display[full].strip()
    s = name.replace("_", " ")
    return re.sub(r"\s+", " ", s).strip()


def categorize(rel: str, name: str) -> str | None:
    path = rel.replace("\\", "/").lower()
    if SKIP_NAMES.search(name):
        return None
    if SKIP_PATH.search(path):
        return None
    if path.startswith("attachments/") or name.endswith("_Attachment"):
        return "Weapon ACC"
    if path.startswith("ammunition/"):
        return "Ammo"
    if path.startswith("weapons/"):
        if name in ("MASTERKEY", "MASTERKEY_Weapon"):
            return "Weapon ACC"
        return "Weapons"
    return None


def default_price(category: str, name: str) -> int:
    low = name.lower()
    if category == "Weapons":
        if any(x in low for x in ("deagle", "launcher", "m203", "aa12", "m60", "pkm")):
            return 2200
        return 1200
    if category == "Ammo":
        if any(x in low for x in ("box", "magazine", "drum", "speedloader")):
            return 80
        return 40
    if category == "Weapon ACC":
        if "scope" in low or "optic" in low:
            return 350
        return 200
    return 100


def parse_vanilla(path: Path) -> dict[str, tuple[str, int, str]]:
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
        items[item_type] = (label, int(price), category)
    return items


def collect_marz_items(display: dict[str, str]) -> dict[str, tuple[str, int, str]]:
    root = resolve_marz_root()
    items: dict[str, tuple[str, int, str]] = {}
    for path in sorted(root.rglob("*.txt")):
        rel = str(path.relative_to(root))
        if SKIP_PATH.search(rel.replace("\\", "/")):
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = ITEM_RE.match(line)
            if not m:
                continue
            name = m.group(1)
            if SKIP_NAMES.search(name):
                continue
            cat = categorize(rel, name)
            if not cat:
                continue
            full = f"{MODULE}.{name}"
            if full in items:
                continue
            items[full] = (label_from_name(name, display), default_price(cat, name), cat)
    return items


def write_shop_list(path: Path, rows: dict[str, tuple[str, int, str]], header: str) -> None:
    lines = [header.rstrip(), ""]
    order = {
        "Weapons": 0, "Ammo": 1, "Weapon ACC": 2, "Food": 3, "Tools": 4,
        "Medical": 5, "Vehicle Parts": 6, "Armor": 7, "Clothes": 8,
    }
    for item_type in sorted(rows, key=lambda k: (order.get(rows[k][2], 9), rows[k][0].lower())):
        label, price, cat = rows[item_type]
        lines.append(f"{item_type}|{label}|{price}|{cat}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    display = load_display_names()
    vanilla: dict[str, tuple[str, int, str]] = {}
    for src in (VANILLA_BUY, VANILLA_EXTRA):
        vanilla.update(parse_vanilla(src))
    marz = collect_marz_items(display)

    buy = dict(vanilla)
    buy.update(marz)

    sell: dict[str, tuple[str, int, str]] = {}
    for item, (label, price, cat) in buy.items():
        sell[item] = (label, max(1, int(price * 0.2)), cat)

    marz_sell = {k: v for k, v in sell.items() if k.startswith("MarzGuns.")}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_shop_list(
        OUT_DIR / "buy_list.txt",
        buy,
        "# IKappaID Phone Shop — buy list (vanilla + MarzGuns)\n"
        "# COPY THIS FILE to .../phoneshop/buy_list.txt",
    )
    write_shop_list(
        OUT_DIR / "sell_list.txt",
        sell,
        "# IKappaID Phone Shop — sell list (~20% buy)\n"
        "# COPY THIS FILE to .../phoneshop/sell_list.txt",
    )
    write_shop_list(
        OUT_DIR / "buy_list_MarzGuns_only.txt",
        marz,
        "# MarzGuns-only buy list (318 items) — for testing or merge\n"
        "# Example lines use MarzGuns.DEAGLE not Base.DEAGLE",
    )
    write_shop_list(
        OUT_DIR / "sell_list_MarzGuns_only.txt",
        marz_sell,
        "# MarzGuns-only sell list",
    )

    marz_lines = [k for k in buy if k.startswith("MarzGuns.")]
    verify = [
        "IKappaID Phone Shop — list verification",
        f"buy_list.txt size check: expect ~21 KB, NOT ~4 KB",
        f"MarzGuns lines in buy_list.txt: {len(marz_lines)}",
        f"Base.* lines in buy_list.txt: {len(buy) - len(marz_lines)}",
        f"Total buy: {len(buy)}",
        "",
        "Sample MarzGuns IDs (must appear in buy_list.txt):",
    ]
    for sample in ("MarzGuns.DEAGLE", "MarzGuns.AA12", "MarzGuns.MP5", "MarzGuns.AK47"):
        row = buy.get(sample)
        verify.append(f"  {sample} = {row[0] if row else 'MISSING'}")
    (OUT_DIR / "VERIFICATION.txt").write_text("\n".join(verify) + "\n", encoding="utf-8")

    print(f"MarzGuns: {len(marz)}, vanilla: {len(vanilla)}, total buy: {len(buy)}")
    print(f"Wrote -> {OUT_DIR}")


if __name__ == "__main__":
    main()
