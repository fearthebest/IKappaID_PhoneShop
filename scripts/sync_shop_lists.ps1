# Copy phoneshop list files to every location the game may load from.
# Required when subscribed to your own Steam Workshop item (Steam cache overrides Zomboid\Workshop).

$ErrorActionPreference = "Stop"

$src = "c:\Users\mpass\Zomboid\Workshop\IKappaID_PhoneShop\Contents\mods\IKappaID_PhoneShop\42\media\phoneshop"
$dests = @(
    "c:\Users\mpass\Desktop\PhoneShop_Workshop\PhoneShop_Workshop\Contents\mods\IKappaID_PhoneShop\42\media\phoneshop",
    "B:\SteamLibrary\steamapps\workshop\content\108600\3749926419\mods\IKappaID_PhoneShop\42\media\phoneshop",
    "c:\Users\mpass\Downloads\ABDM\Documents"
)

$files = @("buy_list.txt", "sell_list.txt", "currency_list.txt", "vehicle_list.txt", "costume_list.txt")

foreach ($dest in $dests) {
    if (-not (Test-Path $dest)) {
        New-Item -ItemType Directory -Path $dest -Force | Out-Null
    }
    foreach ($f in $files) {
        $from = Join-Path $src $f
        if (Test-Path $from) {
            Copy-Item $from (Join-Path $dest $f) -Force
        }
    }
    Write-Host "Synced -> $dest"
}

$buy = Join-Path $src "buy_list.txt"
$lines = (Select-String -Path $buy -Pattern '^\w+\.\w+\|' | Measure-Object).Count
Write-Host "Done. buy_list item lines: $lines"
Write-Host "Restart the game fully (not just reconnect) after editing lists."
