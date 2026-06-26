IKappaID Phone Shop — server presets (FileZilla)

Generated for mod loadout: ModLoadOrder_Export_20260622_211622.txt

FILES
  vehicle_list.txt   — 430 pink-slip vehicles (vanilla + KI5/ATA/MZ/etc.)
  costume_list.txt   — 130 UmaBoid costumes

UPLOAD TARGET (dedicated server)
  Zomboid/media/mods/IKappaID_PhoneShop/42/media/phoneshop/
  — or your Workshop mirror with the same path under Contents/mods/

After upload:
  1. Restart the dedicated server fully.
  2. Clients need the same files (Workshop re-upload or matching folder).

OPTIONAL local sync:
  Copy into:
    PhoneShop_Workshop\...\media\phoneshop\
    Zomboid\Workshop\IKappaID_PhoneShop\...\media\phoneshop\
  Then run: scripts\sync_shop_lists.ps1

NOTES
  - Vehicles only show when that vehicle mod is loaded in the save.
  - Edit prices/labels in the txt files anytime; lines starting with # are ignored.
  - Remove lines you do not want on the server before uploading.
