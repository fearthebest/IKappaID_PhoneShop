-- PhoneShop settings — edit shop items in media/phoneshop/*.txt

PhoneShopConfig = {}

PhoneShopConfig.CurrencyItem  = "Base.Money"
PhoneShopConfig.BundleItem    = "Base.MoneyBundle"
PhoneShopConfig.BundleValue   = 100

PhoneShopConfig.PhoneItem = "CordlessPhone"

PhoneShopConfig.OpenDuration  = 90
PhoneShopConfig.CloseDuration = 90

PhoneShopConfig.HaloOpen  = "... (calling IKappaID Shop)"
PhoneShopConfig.HaloClose = "Okay, thanks for shopping! Happy surviving. Don't die!"

PhoneShopConfig.Categories = {
    "Weapons", "Ammo", "Weapon ACC", "Food",
    "Tools", "Medical", "Vehicle Parts", "Vehicles", "Costume",
    "Armor", "Clothes",
}

-- List loading: set false if you maintain everything only in buy_list / sell_list.
PhoneShopConfig.MergeVehiclesIntoBuy = true
PhoneShopConfig.MergeCostumesIntoBuy = true
PhoneShopConfig.AutoSellCostumes = true

-- Reject buys when the item/vehicle script is missing (mods not loaded on server).
PhoneShopConfig.ValidateItemsOnTrade = true

-- Trade logs (txt under each game save / dedicated server world)
PhoneShopConfig.LogEnabled = true
PhoneShopConfig.LogFolder = "IKappaID_PhoneShop_Logs"
PhoneShopConfig.LogUseSandbox = true
PhoneShopConfig.LogFailedTrades = false
PhoneShopConfig.LogRecentCount = 30

PhoneShopConfig.BuyList  = {}
PhoneShopConfig.SellList = {}
