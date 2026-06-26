# IKappaID Phone Shop

Buy and sell items with a **Cordless Phone** — a survivor market trader for **Project Zomboid Build 42**.

| | |
|---|---|
| **Steam Workshop** | [IKappaID Phone Shop](https://steamcommunity.com/sharedfiles/filedetails/?id=3749926419) |
| **Mod ID** | `IKappaID_PhoneShop` |
| **Build** | B42.19.0+ (`modversion` 1.0.4) |
| **Author** | [IKappaID](https://ko-fi.com/ikappaid) |

---

## List Editor (server admins)

The mod ships editable plain-text shop lists. To **scan gun/item mods** and merge them into buy/sell lists, use the separate **List Editor** tool:

### [Download List Editor (latest release)](https://github.com/fearthebest/IKappaID_PhoneShop/releases/latest)

Unzip → run `run.bat` → point at your `phoneshop` folder → scan mods → write lists.

Full guide: **[LIST_EDITOR.md](LIST_EDITOR.md)**

> Why not on Steam? The PZ Workshop uploader blocks `.bat`, `.exe`, `.zip`, and similar extensions. The editor is hosted here on GitHub Releases instead.

---

## Mod features

- Clean buy/sell shop UI (dark theme, orange accents)
- Generic item presets, ready out of the box
- Pay with cash, money bundles, or jewelry
- Container-aware payments (money in bags and containers counts)
- Multiplayer-ready, server-authoritative trading
- Admin trade logs per world
- Editable buy/sell lists (`42/media/phoneshop/*.txt`)
- Optional **IKST Economy** compatibility when that mod is active
- Vehicles & Costume tabs (pink-slip style lists)

---

## For players

Subscribe on [Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3749926419) and enable **IKappaID Phone Shop** in the mod list.

---

## For server admins

**Trade logs:** `IKappaID_PhoneShop_Logs/ADMIN.txt` on the dedicated server (per world).

**Shop lists:** edit `buy_list.txt`, `sell_list.txt`, etc. under:

```text
PhoneShop_Workshop/Contents/mods/IKappaID_PhoneShop/42/media/phoneshop/
```

Or use the **[List Editor](https://github.com/fearthebest/IKappaID_PhoneShop/releases/latest)** (recommended for large gun-mod merges).

After any list change: restart game/server; in MP, keep lists identical on server and all clients.

Admin notes in-game: `42/media/phoneshop/SHOP_GUIDE.txt` (dev copy; not shipped on Workshop).

---

## Repository layout

```text
PhoneShop_Workshop/
├── README.md                 ← you are here
├── LIST_EDITOR.md            ← List Editor guide + download link
├── PhoneShop_Workshop/
│   ├── workshop.txt          ← Steam Workshop metadata (upload source)
│   └── Contents/mods/IKappaID_PhoneShop/
│       ├── common/           ← required for B42 (may be empty)
│       ├── mod.info
│       └── 42/               ← Lua, media, phoneshop lists
├── tools/ShopListEditor/     ← List Editor source (UI)
├── scripts/
│   ├── shop_core/            ← shared Python library
│   ├── build_list_editor_zip.py
│   └── package_workshop_ship.py
└── presets/                  ← optional list presets for hosts
```

---

## Development

**Package for Steam upload** (strips dev-only files, ensures `common/`, blocks forbidden extensions):

```bat
python scripts\package_workshop_ship.py
```

Target folder: `%UserProfile%\Zomboid\Workshop\IKappaID_PhoneShop`

**Build List Editor zip for GitHub Releases:**

```bat
python scripts\build_list_editor_zip.py
```

Output: `dist/IKappaID_PhoneShop_ListEditor.zip`

---

## Links

- GitHub: https://github.com/fearthebest/IKappaID_PhoneShop
- Steam Workshop: https://steamcommunity.com/sharedfiles/filedetails/?id=3749926419
- Ko-fi: https://ko-fi.com/ikappaid
