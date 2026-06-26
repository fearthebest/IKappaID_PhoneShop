# IKappaID Phone Shop

A survivor market trader system for Project Zomboid Build 42. Players buy and sell items through a Cordless Phone interface with server-authoritative transactions.

[![Steam Workshop](https://img.shields.io/badge/Steam-Workshop-blue)](https://steamcommunity.com/sharedfiles/filedetails/?id=3749926419)
[![Version](https://img.shields.io/badge/Version-1.0.4-green)](https://github.com/fearthebest/IKappaID_PhoneShop/releases)
[![Build](https://img.shields.io/badge/Project%20Zomboid-Build%2042-orange)](https://pzwiki.net/wiki/Build_42)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

IKappaID Phone Shop provides a server-authoritative trading platform with a dark-themed UI. It supports container-aware currency detection, plain-text shop lists, and integration with IKST Economy.

## Features

- Dark-themed buy/sell interface with category filtering and search
- Currency handling: cash, money bundles, and jewelry; detects currency inside bags and containers
- Multiplayer-optimized server-authoritative transactions
- Extensible plain-text shop lists for easy server customization
- Administrative Shop List Editor for scanning third-party mods
- Vehicle and costume tabs for pink slips and cosmetic items

## Repository structure

```text
.
├── README.md
├── LIST_EDITOR.md             # Admin tool guide
├── LICENSE
├── PhoneShop_Workshop/        # Mod source (Lua, media, shop lists)
│   └── Contents/mods/IKappaID_PhoneShop/42/
├── tools/ShopListEditor/      # Desktop list editor source
├── scripts/                   # Packaging and build automation
└── presets/                   # Pre-configured shop lists
```

## Server administration

### Shop List Editor

Automated inventory management tool. Scans mod `media/scripts` for item definitions and merges them into the Phone Shop database with custom pricing.

- **Download:** [Latest Release](https://github.com/fearthebest/IKappaID_PhoneShop/releases/latest)
- **Documentation:** [LIST_EDITOR.md](LIST_EDITOR.md)

The List Editor is hosted on GitHub because the Steam Workshop uploader restricts executables and batch files.

### Manual configuration

Shop inventories are located at:

`PhoneShop_Workshop/Contents/mods/IKappaID_PhoneShop/42/media/phoneshop/`

| File | Description |
|------|-------------|
| `buy_list.txt` | Items available for purchase |
| `sell_list.txt` | Items players can sell to the shop |
| `currency_list.txt` | Valid currency items and their values |
| `vehicle_list.txt` | Vehicle inventory definitions |

## Development

**Package for Steam Workshop:**

```powershell
python scripts/package_workshop_ship.py
```

**Build List Editor release zip:**

```powershell
python scripts/build_list_editor_zip.py
```

## License

MIT License — see [LICENSE](LICENSE).

## Links

- **Steam Workshop:** https://steamcommunity.com/sharedfiles/filedetails/?id=3749926419
- **Support:** https://ko-fi.com/ikappaid
- **Source:** https://github.com/fearthebest/IKappaID_PhoneShop

Community mod — not affiliated with or endorsed by The Indie Stone.
