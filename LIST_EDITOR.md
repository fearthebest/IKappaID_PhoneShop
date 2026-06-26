# Shop List Editor

The Shop List Editor is a Windows-based utility designed to streamline the management of IKappaID Phone Shop inventories. It automates the process of scanning Project Zomboid mods for item definitions and merging them into the shop's buy and sell lists.

---

## System Requirements

*   **Operating System**: Windows 10 or 11.
*   **Environment**: [Python 3.10+](https://www.python.org/downloads/) (Must be added to System PATH).
*   **Dependencies**: The tool requires `customtkinter`, which is automatically installed upon the first execution of `run.bat`.

---

## Installation and Setup

1.  Download the `IKappaID_PhoneShop_ListEditor.zip` from the [Releases](https://github.com/fearthebest/IKappaID_PhoneShop/releases) page.
2.  Extract the archive to a local directory.
3.  Execute `run.bat` to launch the application.

---

## Usage Workflow

1.  **Directory Detection**: The tool attempts to auto-locate your Phone Shop installation. If it fails, use the **Browse** button to select the `phoneshop` directory manually.
2.  **Baseline Creation**: It is recommended to click **Save vanilla baseline** before making significant changes.
3.  **Mod Scanning**: Select the root directory of the mod you wish to import items from and click **Scan mod**.
4.  **Inventory Selection**:
    *   Toggle items by double-clicking their entry in the table.
    *   Adjust prices and categories directly within the interface.
5.  **Deployment**: Click **WRITE BUY + SELL LISTS** to commit changes.
6.  **Synchronization**: Use the "Sync all folders" option to propagate changes to both your local mod folder and your Workshop upload directory.

---

## Technical Specifications

### List Format
The editor generates entries using the following pipe-delimited format:
`itemType|label|price|category`

*Example*: `Base.Axe|Hand Axe|25|Tools`

### Synchronization and Backups
*   **Backups**: Every write operation generates a `.bak` file in the target directory.
*   **Multiplayer**: To prevent client-side desynchronization, the `buy_list.txt` and `sell_list.txt` must be identical on the server and all connected clients.

---

## Troubleshooting

*   **Python Not Found**: Ensure Python is correctly installed and the "Add to PATH" option was selected during installation.
*   **Permission Errors**: Ensure the tool has write access to the Zomboid Workshop and mod directories.
