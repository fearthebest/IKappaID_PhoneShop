# IKappaID Phone Shop — List Editor

Dark-themed desktop tool to scan gun/item mods and merge into `buy_list.txt` / `sell_list.txt`.

## Requirements

- Python 3.10+
- `customtkinter` (installed automatically by `run.bat`)

```bat
pip install -r tools\ShopListEditor\requirements.txt
```

## Run

**From GitHub zip** (recommended for server admins):

```bat
run.bat
```

Or: `python launch.py`

**Dev repo:**

```bat
tools\ShopListEditor\run.bat
```

Steam Workshop **cannot** ship this tool — the in-game uploader blocks `.bat`, `.exe`, `.zip`, etc. Host the zip on [GitHub Releases](https://github.com/fearthebest/IKappaID_PhoneShop/releases).

## Features (v1.1)

- **Dark UI** — matches Phone Shop (charcoal + orange)
- **Auto-detect** Phone Shop `phoneshop` folder (Workshop / dev / Steam)
- **Scan** PZ mod `media/scripts` for `item` definitions
- **Hide junk** — spawners, `*_Weapon`, fx paths
- **WRITE BUY + SELL LISTS** — large orange bar at the bottom (always visible)
- **Vanilla baseline** — save/restore known-good lists under `phoneshop/.phoneshop_editor/vanilla_baseline/`
- **Sync all folders** after write (optional checkbox)
- **Undo** — restore latest `.bak` files

## Workflow

1. Source mod folder → **Scan mod**
2. Phone Shop folder auto-filled → **Detect** if needed
3. Edit prices/categories; double-click ✓ to include/exclude
4. **Write lists** → confirm preview → optional sync

## Limits

- Script-based items only (not WorldDictionary / GaelGun `Base.*` yet)
- `vehicle_list.txt` / `costume_list.txt` copied on sync but not edited in UI

## Library

`scripts/shop_core/` — shared with CLI builders.
