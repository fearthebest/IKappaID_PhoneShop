# IKappaID Phone Shop

A survivor market trader system for Project Zomboid Build 42, allowing players to buy and sell items using a Cordless Phone interface.

[![Steam Workshop](https://img.shields.io/badge/Steam-Workshop-blue)](https://steamcommunity.com/sharedfiles/filedetails/?id=3749926419)
[![Version](https://img.shields.io/badge/Version-1.0.4-green)](https://github.com/fearthebest/IKappaID_PhoneShop/releases)
[![Build](https://img.shields.io/badge/Project%20Zomboid-Build%2042-orange)](https://pzwiki.net/wiki/Build_42)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

IKappaID Phone Shop provides a server-authoritative trading platform. It features a modern, dark-themed user interface and supports complex payment logic, including container-aware currency detection and integration with the IKST Economy mod.

## Core Features

*   **Advanced UI**: Dark-themed buy/sell interface with category filtering and search.
*   **Currency Handling**: Supports cash, money bundles, and jewelry. Automatically detects currency within bags and containers.
*   **Multiplayer Optimized**: Server-authoritative transactions with synchronization validation to prevent exploits.
*   **Extensible Lists**: All shop inventories are defined in plain-text files, allowing for easy modification and mod integration.
*   **Administrative Tools**: Includes a dedicated desktop utility for scanning third-party mods and generating shop lists.
*   **Vehicle & Costume Support**: Specialized tabs for trading vehicle pink slips and cosmetic items.

---

## Server Administration

### Shop List Editor
For automated inventory management, use the **Shop List Editor**. This tool scans mod files (e.g., weapon or item mods) and merges them into the Phone Shop database with custom pricing.

*   **Download**: [Latest Release (GitHub)](https://github.com/fearthebest/IKappaID_PhoneShop/releases/latest)
*   **Documentation**: [List Editor Guide](LIST_EDITOR.md)

*Note: The List Editor is hosted on GitHub because the Steam Workshop uploader restricts the executable and batch files required for the utility.*

### Manual Configuration
Shop inventories are located in the mod directory:
`Contents/mods/IKappaID_PhoneShop/42/media/phoneshop/`

| File | Description |
|:---|:---|
| `buy_list.txt` | Items available for purchase |
| `sell_list.txt` | Items players can sell to the shop |
| `currency_list.txt` | Valid currency items and their values |
| `vehicle_list.txt` | Vehicle inventory definitions |

---

## Repository Structure

```text
.
├── README.md                 # Project overview
├── LIST_EDITOR.md            # Technical guide for the admin tool
├── LICENSE                   # MIT License
├── PhoneShop_Workshop/       # Mod source files (Lua, Media)
├── tools/ShopListEditor/     # Source code for the desktop utility
├── scripts/                  # Automation scripts for packaging and builds
└── presets/                  # Pre-configured shop lists for common mods
```

## Development and Building

### Packaging for Steam
To prepare the mod for Workshop upload (strips development artifacts and validates structure):
```powershell
python scripts/package_workshop_ship.py
```

### Building the List Editor
To generate a distributable zip for the List Editor:
```powershell
python scripts/build_list_editor_zip.py
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Links

*   **Steam Workshop**: [IKappaID Phone Shop](https://steamcommunity.com/sharedfiles/id=3749926419)
*   **Support**: [Ko-fi](https://ko-fi.com/ikappaid)
*   **Source Code**: [GitHub Repository](https://github.com/fearthebest/IKappaID_PhoneShop)
