# IKappaID Phone Shop — dedicated host upload (read this first)

Your panel path (correct folder):
  .../108600/3749926419/mods/IKappaID_PhoneShop/42/media/phoneshop/

## Why edits "do nothing"

### 1. Files must be HERE, not in presets/
The game only reads list files directly inside phoneshop/.
A presets/ subfolder is ignored. Copy files OUT of presets/ into phoneshop/.

### 2. Missing files on your host (common)
You need ALL of these in phoneshop/:

  buy_list.txt
  sell_list.txt
  currency_list.txt
  vehicle_list.txt      ← Vehicles tab (pink slips) — often missing
  costume_list.txt      ← Costume tab (UmaBoid) — often missing

If vehicle_list.txt / costume_list.txt are missing, Vehicles and Costume tabs stay empty
even if you edit buy_list.txt.

### 3. Your buy_list.txt is probably the OLD small list
Healthy server list: buy_list.txt about 80–85 KB (~1750 lines).
If yours is about 8–9 KB, you still have the old vanilla preset — edits to a few lines
won't match what the admin expects.

Check in-game console when opening the shop:
  [IKappaID_PhoneShop] lists loaded: buy=1750 sell=1775 vehicles=430 costumes=130
If buy= is a small number, the wrong file is still loaded.

### 4. Mod Lua must be 1.0.2+ (not just txt files)
Vehicles / Costume tabs need updated Lua under:
  .../IKappaID_PhoneShop/42/media/lua/shared/PhoneShop_Loader.lua
  .../PhoneShop_PinkSlip.lua
  .../client/PhoneShop_Client.lua
  mod.info → modversion=1.0.2

Uploading only buy_list.txt on an old mod build = no new tabs, no pink-slip minting.

### 5. Multiplayer: EVERY player needs the same files
The shop UI reads lists from each player's local mod copy (Workshop subscribe),
not from the server over the network.

So:
  - Server host files updated ✓
  - Player still subscribed to old Workshop item ✗  → player sees OLD shop

Fix: re-upload Workshop item OR ensure every client uses the same mod folder version.

### 6. Restart required
After any upload: stop server completely, start again.
Players: fully quit game and relaunch (not just disconnect).

---

## What to upload (full pack)

From this repo, upload into phoneshop/ (same folder as buy_list.txt):

  presets/server/vehicle_list.txt   → rename/copy as vehicle_list.txt
  presets/server/costume_list.txt   → rename/copy as costume_list.txt
  (optional) your full buy_list.txt / sell_list.txt from dev build

Or use the smaller curated vehicles file:
  presets/server-curated/vehicle_list.txt → vehicle_list.txt

---

## Quick verification

1. Open shop in game.
2. Command console / logs should show lists loaded with vehicle/costume counts.
3. Vehicles tab: pink-slip entries with vehicle names.
4. Costume tab: UmaBoid outfits (only if UmaBoid_B42_Miroki enabled).
5. Hidden items = mods not enabled on that client — not a txt upload bug.

---

## Do NOT

- Put active lists only inside presets/ (ignored)
- Edit buy_list.txt expecting Vehicles tab to change (use vehicle_list.txt)
- Test with only server updated while clients use old Steam Workshop build
