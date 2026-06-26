# List Editor — IKappaID Phone Shop

**Windows desktop tool for server admins.** Scan gun/item mods and merge entries into Phone Shop `buy_list.txt` / `sell_list.txt`.

> **Download (no Python project setup):** [Latest release zip](https://github.com/fearthebest/IKappaID_PhoneShop/releases/latest)  
> Unzip anywhere, then double-click `run.bat` (or run `python launch.py`).

Steam Workshop **cannot** include this tool — the in-game uploader blocks `.bat`, `.exe`, `.zip`, and similar file types.

---

## Requirements

- Windows 10/11
- [Python 3.10+](https://www.python.org/downloads/) (check **Add python to PATH** during install)
- Internet on first run (`customtkinter` is installed automatically)

---

## Quick start

1. Download **`IKappaID_PhoneShop_ListEditor.zip`** from [Releases](https://github.com/fearthebest/IKappaID_PhoneShop/releases).
2. Unzip to a folder of your choice (Desktop is fine).
3. Run **`run.bat`** or `python launch.py`.
4. The editor auto-detects your Phone Shop `phoneshop` folder (Steam Workshop cache, `Zomboid/mods`, or local Workshop upload).
5. **Save vanilla baseline** once while lists are still good (optional safety net).
6. Set **Source mod folder** to a gun/item mod → **Scan mod**.
7. Double-click rows to include/exclude; edit prices and categories.
8. Click **WRITE BUY + SELL LISTS** (orange bar at the bottom).
9. Restart the game or dedicated server.

---

## Where shop lists live

Inside the mod package:

```text
PhoneShop_Workshop/Contents/mods/IKappaID_PhoneShop/42/media/phoneshop/
```

| File | Purpose |
|------|---------|
| `buy_list.txt` | Items players can buy |
| `sell_list.txt` | Items players can sell |
| `vehicle_list.txt` | Pink-slip vehicles (optional) |
| `costume_list.txt` | Costumes (optional) |
| `currency_list.txt` | Cash / jewelry accepted as payment |

Line format (`buy` / `sell`):

```text
itemType|label|price|category
```

Example:

```text
Base.Axe|Hand Axe|25|Tools
```

---

## Multiplayer

- Use the **same** list files on the **dedicated server** and **every client**.
- Restart server and clients after editing lists.
- Trade logs (separate from lists): `IKappaID_PhoneShop_Logs/ADMIN.txt` per world on the server.

---

## Features

- Dark UI (charcoal + orange) matching the in-game shop
- Auto-detect Phone Shop folder (Workshop / Steam cache / local mods)
- Scan PZ mod `media/scripts` for `item` definitions
- Hide junk filter (spawners, `*_Weapon`, fx paths)
- Vanilla baseline save/restore
- Sync all known Phone Shop folders after write (optional)
- Undo via latest `.bak` files

---

## Limits (v1)

- Script-based items only — not WorldDictionary / GaelGun `Base.*` imports yet
- `vehicle_list.txt` / `costume_list.txt` are copied on sync but not edited in the UI

---

## Run from this repository (developers)

```bat
tools\ShopListEditor\run.bat
```

Rebuild the release zip:

```bat
python scripts\build_list_editor_zip.py
```

Shared library: `scripts/shop_core/`

More detail: `tools/ShopListEditor/START_HERE.txt`
