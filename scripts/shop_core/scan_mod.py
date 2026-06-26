from __future__ import annotations

import json
import re
from pathlib import Path

from .lists import CATEGORY_ORDER
from .models import ScannedItem

ITEM_RE = re.compile(r"^\s*item\s+(\S+)")
MODINFO_ID_RE = re.compile(r"^\s*id\s*=\s*(\S+)", re.I)

DEFAULT_SKIP_NAMES = re.compile(
    r"(?i)^(FakeItem|Bullet_\d+|40mm_HE_Explosion|.*_Explosion|.*_Weapon|TEMP.*)$",
)
DEFAULT_SKIP_PATH = re.compile(
    r"(?i)([/\\]fx[/\\]|[/\\]spawners[/\\]|[/\\]generic\.txt$|ammo_casings\.txt$)",
)

CATEGORY_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)([/\\]attachments[/\\]|_attachment$)"), "Weapon ACC"),
    (re.compile(r"(?i)[/\\]ammunition[/\\]"), "Ammo"),
    (re.compile(r"(?i)[/\\]weapons[/\\]"), "Weapons"),
    (re.compile(r"(?i)(food|drink|snack)"), "Food"),
    (re.compile(r"(?i)(medical|bandage|pill)"), "Medical"),
    (re.compile(r"(?i)(clothing|clothes|jacket|shirt|pants)"), "Clothes"),
    (re.compile(r"(?i)(armor|helmet|vest)"), "Armor"),
    (re.compile(r"(?i)(vehicle|car|truck)"), "Vehicle Parts"),
    (re.compile(r"(?i)(tool|hammer|screwdriver|wrench)"), "Tools"),
]


def find_mod_root(path: Path) -> Path:
    path = path.resolve()
    if path.is_file():
        path = path.parent
    if (path / "mod.info").is_file():
        return path
    for child in path.iterdir():
        if child.is_dir() and (child / "mod.info").is_file():
            return child
    return path


def find_scripts_root(mod_root: Path) -> Path | None:
    candidates: list[Path] = []
    for child in mod_root.iterdir():
        if child.is_dir() and re.match(r"^42(\.\d+)?$", child.name):
            scripts = child / "media" / "scripts"
            if scripts.is_dir():
                candidates.append(scripts)
    direct = mod_root / "media" / "scripts"
    if direct.is_dir():
        candidates.append(direct)
    if not candidates:
        return None
    return max(candidates, key=lambda p: len(str(p)))


def read_mod_id(mod_root: Path) -> str | None:
    for name in ("mod.info", "42/mod.info"):
        info = mod_root / name
        if not info.is_file():
            continue
        for line in info.read_text(encoding="utf-8", errors="replace").splitlines():
            m = MODINFO_ID_RE.match(line)
            if m:
                return m.group(1).strip()
    return None


def detect_module_prefix(mod_root: Path, override: str | None = None) -> str:
    if override and override.strip():
        return override.strip().rstrip(".")
    mod_id = read_mod_id(mod_root)
    if mod_id:
        return mod_id
    return "Base"


def load_display_names(mod_root: Path, module: str) -> dict[str, str]:
    names: dict[str, str] = {}
    patterns = [
        "media/lua/shared/Translate/EN/ItemName_EN.txt",
        "media/lua/shared/translate/EN/ItemName_EN.txt",
        "media/lua/shared/Translate/EN/ItemName.json",
        "media/lua/shared/translate/EN/itemname_en.txt",
    ]
    roots = [mod_root]
    for child in mod_root.iterdir():
        if child.is_dir() and re.match(r"^42(\.\d+)?$", child.name):
            roots.append(child)
    for root in roots:
        for rel in patterns:
            path = root / Path(rel.replace("/", "\\") if "\\" in str(root) else rel)
            if not path.is_file():
                path = root / rel
            if not path.is_file():
                continue
            if path.suffix.lower() == ".json":
                data = json.loads(path.read_text(encoding="utf-8"))
                for k, v in data.items():
                    if str(k).startswith(module + ".") or module == "Base":
                        names[str(k)] = str(v).strip()
            else:
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                    line = line.strip()
                    if "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    if key.startswith(module + ".") or module == "Base":
                        names[key] = val.strip().strip('"')
    return names


def label_for(module: str, name: str, display: dict[str, str]) -> str:
    full = f"{module}.{name}" if module != "Base" else f"Base.{name}"
    if full in display and display[full].strip():
        return display[full].strip()
    if module != "Base":
        alt = f"{module}.{name}"
        if alt in display and display[alt].strip():
            return display[alt].strip()
    return re.sub(r"\s+", " ", name.replace("_", " ")).strip()


def categorize(rel_path: str, name: str) -> str | None:
    if DEFAULT_SKIP_NAMES.search(name):
        return None
    if DEFAULT_SKIP_PATH.search(rel_path.replace("\\", "/")):
        return None
    rel = rel_path.replace("\\", "/")
    for pattern, cat in CATEGORY_RULES:
        if pattern.search(rel) or pattern.search(name):
            return cat
    if name.lower().endswith("mag") or "magazine" in name.lower():
        return "Ammo"
    if "scope" in name.lower() or "optic" in name.lower():
        return "Weapon ACC"
    return "Weapons"


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
    if category == "Food":
        return 10
    if category == "Medical":
        return 25
    if category == "Tools":
        return 50
    if category == "Clothes":
        return 80
    if category == "Armor":
        return 150
    return 100


def scan_mod_folder(
    mod_path: Path,
    *,
    module_prefix: str | None = None,
    sell_ratio_hint: float = 0.2,
) -> tuple[list[ScannedItem], str, Path | None]:
    mod_root = find_mod_root(mod_path)
    module = detect_module_prefix(mod_root, module_prefix)
    scripts = find_scripts_root(mod_root)
    if not scripts:
        raise FileNotFoundError(
            f"No media/scripts folder found under {mod_root}\n"
            "Point at a PZ mod folder (with mod.info and 42/media/scripts)."
        )
    display = load_display_names(mod_root, module)
    found: dict[str, ScannedItem] = {}
    for path in sorted(scripts.rglob("*.txt")):
        rel = str(path.relative_to(scripts))
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = ITEM_RE.match(line)
            if not m:
                continue
            name = m.group(1)
            cat = categorize(rel, name)
            if not cat:
                continue
            if module == "Base":
                item_type = f"Base.{name}"
            else:
                item_type = f"{module}.{name}"
            if item_type in found:
                continue
            found[item_type] = ScannedItem(
                item_type=item_type,
                label=label_for(module, name, display),
                price=default_price(cat, name),
                category=cat,
                source=rel,
                included=True,
            )
    items = list(found.values())
    items.sort(key=lambda r: (CATEGORY_ORDER.get(r.category, 99), r.label.lower()))
    return items, module, scripts
