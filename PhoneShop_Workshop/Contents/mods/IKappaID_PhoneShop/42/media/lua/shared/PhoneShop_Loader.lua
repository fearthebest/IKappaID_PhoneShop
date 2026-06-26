-- PhoneShop — load shop lists from text files

require "PhoneShop_Shared"
require "PhoneShop_Config"

local VALID = {}
for _, cat in ipairs(PhoneShopConfig.Categories or {}) do
    VALID[cat] = true
end

PhoneShop.lastLoadStats = PhoneShop.lastLoadStats or {}

local function trim(s)
    return s and s:match("^%s*(.-)%s*$") or s
end

local function readModLines(path)
    local lines = {}
    if type(getModFileReader) ~= "function" or not path or path == "" then
        return lines
    end
    local reader = getModFileReader(PhoneShop.MOD_ID, path, false)
    if not reader then
        return lines
    end
    local readLine = reader.readLine
    if type(readLine) ~= "function" then
        return lines
    end
    while true do
        local line = readLine(reader)
        if line == nil then
            break
        end
        lines[#lines + 1] = tostring(line)
    end
    local closeFn = reader.close
    if type(closeFn) == "function" then
        closeFn(reader)
    end
    return lines
end

local function dedupeEntries(list)
    local byType = {}
    local order = {}
    for _, e in ipairs(list) do
        local itemType = e.itemType
        if itemType then
            if not byType[itemType] then
                order[#order + 1] = itemType
            end
            byType[itemType] = e
        end
    end
    local out = {}
    for i = 1, #order do
        out[i] = byType[order[i]]
    end
    return out
end

local function dedupeCurrency(list)
    local byType = {}
    local order = {}
    for _, e in ipairs(list) do
        if e.itemType then
            if not byType[e.itemType] then
                order[#order + 1] = e.itemType
            end
            byType[e.itemType] = e
        end
    end
    local out = {}
    for i = 1, #order do
        out[i] = byType[order[i]]
    end
    return out
end

local function readList(path, statsKey)
    local list = {}
    local stats = { skipped = 0, lines = 0 }
    for _, line in ipairs(readModLines(path)) do
        if line ~= "" and line:sub(1, 1) ~= "#" then
            stats.lines = stats.lines + 1
            local itemType, label, price, category = line:match("^([^|]+)|([^|]+)|(%d+)|([^|]+)$")
            itemType = trim(itemType)
            label = trim(label)
            category = trim(category)
            price = tonumber(price)
            if itemType and label and price and category and VALID[category] then
                list[#list + 1] = {
                    itemType = itemType,
                    label    = label,
                    price    = price,
                    category = category,
                }
            else
                stats.skipped = stats.skipped + 1
            end
        end
    end
    if statsKey then
        PhoneShop.lastLoadStats[statsKey] = stats
    end
    return dedupeEntries(list)
end

local function readVehicleList(path)
    local list = {}
    local stats = { skipped = 0, lines = 0 }
    local tag = PhoneShop.PINKSLIP_TAG or "@ps:"
    for _, line in ipairs(readModLines(path)) do
        if line ~= "" and line:sub(1, 1) ~= "#" then
            stats.lines = stats.lines + 1
            local scriptName, label, price, hasKey = line:match("^([^|]+)|([^|]+)|(%d+)|(%d+)$")
            scriptName = trim(scriptName)
            label = trim(label)
            price = tonumber(price)
            hasKey = tonumber(hasKey)
            if scriptName and label and price then
                local shopKey = tag .. scriptName
                list[#list + 1] = {
                    itemType = shopKey,
                    label = label,
                    price = price,
                    category = "Vehicles",
                    vehicleScript = scriptName,
                    hasKey = hasKey == 1,
                    kind = "pinkslip",
                }
            else
                stats.skipped = stats.skipped + 1
            end
        end
    end
    PhoneShop.lastLoadStats.vehicles = stats
    return dedupeEntries(list)
end

local function readCostumeList(path)
    local list = {}
    local stats = { skipped = 0, lines = 0 }
    for _, line in ipairs(readModLines(path)) do
        if line ~= "" and line:sub(1, 1) ~= "#" then
            stats.lines = stats.lines + 1
            local itemType, label, price = line:match("^([^|]+)|([^|]+)|(%d+)$")
            itemType = trim(itemType)
            label = trim(label)
            price = tonumber(price)
            if itemType and label and price then
                list[#list + 1] = {
                    itemType = itemType,
                    label = label,
                    price = price,
                    category = "Costume",
                }
            else
                stats.skipped = stats.skipped + 1
            end
        end
    end
    PhoneShop.lastLoadStats.costumes = stats
    return dedupeEntries(list)
end

local function indexByType(list)
    local map = {}
    for _, e in ipairs(list) do
        map[e.itemType] = e
    end
    return map
end

local function mergeLists(base, extra)
    local seen = {}
    for _, e in ipairs(base) do
        seen[e.itemType] = true
    end
    for _, e in ipairs(extra) do
        if not seen[e.itemType] then
            base[#base + 1] = e
            seen[e.itemType] = true
        end
    end
    return base
end

local function readCurrency(path)
    local list = {}
    local stats = { skipped = 0, lines = 0 }
    for _, line in ipairs(readModLines(path)) do
        if line ~= "" and line:sub(1, 1) ~= "#" then
            stats.lines = stats.lines + 1
            local itemType, worth = line:match("^([^|]+)|(%d+)$")
            itemType = trim(itemType)
            worth = tonumber(worth)
            if itemType and worth and worth > 0 then
                list[#list + 1] = { itemType = itemType, worth = worth }
            else
                stats.skipped = stats.skipped + 1
            end
        end
    end
    PhoneShop.lastLoadStats.currency = stats
    return dedupeCurrency(list)
end

local function invalidateClientCaches()
    if PhoneShopClient and PhoneShopClient.resetItemCaches then
        PhoneShopClient.resetItemCaches()
    end
end

function PhoneShop.listFingerprint()
    local buy = PhoneShopConfig.BuyList or {}
    local sell = PhoneShopConfig.SellList or {}
    local sum = 0
    for _, e in ipairs(buy) do
        sum = sum + (tonumber(e.price) or 0)
    end
    for _, e in ipairs(sell) do
        sum = sum + (tonumber(e.price) or 0)
    end
    return string.format("%d:%d:%d", #buy, #sell, sum)
end

function PhoneShop.getListInfo()
    return {
        revision = PhoneShop.listRevision or 0,
        fingerprint = PhoneShop.listFingerprint(),
        buyCount = #(PhoneShopConfig.BuyList or {}),
        sellCount = #(PhoneShopConfig.SellList or {}),
    }
end

function PhoneShop.reloadShopLists()
    local buy = readList("media/phoneshop/buy_list.txt", "buy")
    local vehicles = readVehicleList("media/phoneshop/vehicle_list.txt")
    local costumes = readCostumeList("media/phoneshop/costume_list.txt")

    if PhoneShopConfig.MergeVehiclesIntoBuy ~= false then
        mergeLists(buy, vehicles)
    end
    if PhoneShopConfig.MergeCostumesIntoBuy ~= false then
        mergeLists(buy, costumes)
    end

    PhoneShopConfig.BuyList = buy
    PhoneShopConfig.VehicleList = vehicles
    PhoneShopConfig.CostumeList = costumes
    PhoneShopConfig.BuyByType = indexByType(buy)

    local sell = readList("media/phoneshop/sell_list.txt", "sell")
    if PhoneShopConfig.AutoSellCostumes ~= false then
        local sellExtras = {}
        for _, e in ipairs(costumes) do
            sellExtras[#sellExtras + 1] = {
                itemType = e.itemType,
                label = e.label,
                price = math.max(1, math.floor(e.price * 0.2)),
                category = e.category,
            }
        end
        mergeLists(sell, sellExtras)
    end
    PhoneShopConfig.SellList = sell
    PhoneShopConfig.SellByType = indexByType(sell)

    PhoneShopConfig.CurrencyList = readCurrency("media/phoneshop/currency_list.txt")
    if #PhoneShopConfig.CurrencyList == 0 then
        PhoneShopConfig.CurrencyList = {
            { itemType = PhoneShopConfig.CurrencyItem or "Base.Money", worth = 1 },
            { itemType = PhoneShopConfig.BundleItem or "Base.MoneyBundle", worth = PhoneShopConfig.BundleValue or 100 },
        }
    end

    PhoneShop.listRevision = (PhoneShop.listRevision or 0) + 1
    invalidateClientCaches()

    if print then
        local buyCount = #PhoneShopConfig.BuyList
        local sellCount = #PhoneShopConfig.SellList
        local fp = PhoneShop.listFingerprint()
        print(string.format(
            "[IKappaID_PhoneShop] lists loaded rev=%d buy=%d sell=%d vehicles=%d costumes=%d fp=%s",
            PhoneShop.listRevision,
            buyCount,
            sellCount,
            #vehicles,
            #costumes,
            fp
        ))
        local function warnSkipped(key, label)
            local st = PhoneShop.lastLoadStats[key]
            if st and st.skipped > 0 then
                print(string.format(
                    "[IKappaID_PhoneShop] WARN: %s — %d line(s) skipped (bad format or unknown category)",
                    label, st.skipped
                ))
            end
        end
        warnSkipped("buy", "buy_list.txt")
        warnSkipped("sell", "sell_list.txt")
        warnSkipped("vehicles", "vehicle_list.txt")
        warnSkipped("costumes", "costume_list.txt")
        warnSkipped("currency", "currency_list.txt")
        if buyCount == 0 and sellCount == 0 then
            print("[IKappaID_PhoneShop] WARN: buy and sell lists are empty — check media/phoneshop/*.txt path and mod ID")
        end
    end
end

PhoneShop.reloadShopLists()
