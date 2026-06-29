-- PhoneShop — money + buy/sell
-- Raw cash: getCashOnly / payCashOnly / giveCashOnly (inventory items only).
-- Public API: when IKST Economy is active, getMoney/canAfford/pay delegate to Economy.

require "PhoneShop_Shared"
require "PhoneShop_Config"
require "PhoneShop_Loader"
require "PhoneShop_Log"
require "PhoneShop_PinkSlip"

local function bundleValue()
    return PhoneShopConfig.BundleValue or PhoneShop.BUNDLE_VALUE
end

local function currency()
    return PhoneShopConfig.CurrencyItem or PhoneShop.CURRENCY
end

local function bundleItem()
    return PhoneShopConfig.BundleItem or PhoneShop.BUNDLE
end

local function getInv(player)
    return player and player:getInventory() or nil
end

local function markDirty(inv)
    if inv and inv.setDrawDirty then
        inv:setDrawDirty(true)
    end
end

local function syncAdd(inv, item)
    if item and sendAddItemToContainer then
        sendAddItemToContainer(inv, item)
    end
end

local function syncRemove(inv, item)
    if item and sendRemoveItemFromContainer then
        sendRemoveItemFromContainer(inv, item)
    end
end

local function addItem(inv, itemType)
    if not inv or not itemType then return nil end
    local item = inv:AddItem(itemType)
    syncAdd(inv, item)
    return item
end

local function removeItem(inv, item)
    if not inv or not item then return end
    inv:Remove(item)
    syncRemove(inv, item)
end

local function collectMoney(player)
    local inv = getInv(player)
    if not inv then return {} end
    local out = {}
    for _, cur in ipairs(PhoneShopConfig.CurrencyList or {}) do
        local items = inv:getItemsFromType(cur.itemType, true)
        if items then
            for i = 0, items:size() - 1 do
                local item = items:get(i)
                table.insert(out, {
                    inv = item:getContainer() or inv,
                    item = item,
                    worth = cur.worth,
                })
            end
        end
    end
    return out
end

local function payEntries(entries, price)
    table.sort(entries, function(a, b)
        if a.worth ~= b.worth then return a.worth < b.worth end
        return false
    end)
    local spent = 0
    local used = {}
    for _, e in ipairs(entries) do
        if spent >= price then break end
        table.insert(used, e)
        spent = spent + e.worth
    end
    if spent < price then return false, 0, 0 end
    for _, e in ipairs(used) do
        removeItem(e.inv, e.item)
    end
    return true, spent - price, spent
end

local function undoCashAdds(inv, added)
    for i = #added, 1, -1 do
        removeItem(inv, added[i])
    end
end

function PhoneShop.getCashOnly(player)
    player = PhoneShop.resolvePlayer(player)
    if not player then
        return 0
    end
    local total = 0
    for _, e in ipairs(collectMoney(player)) do
        total = total + e.worth
    end
    return total
end

function PhoneShop.giveCashOnly(player, amount)
    amount = math.floor(tonumber(amount) or 0)
    if amount <= 0 then return true end
    player = PhoneShop.resolvePlayer(player)
    local inv = getInv(player)
    if not inv then return false end
    local bv = bundleValue()
    local added = {}
    local function tryAdd(itemType)
        local item = addItem(inv, itemType)
        if item then
            added[#added + 1] = item
            return true
        end
        return false
    end
    for _ = 1, math.floor(amount / bv) do
        if not tryAdd(bundleItem()) then
            undoCashAdds(inv, added)
            return false
        end
    end
    for _ = 1, amount % bv do
        if not tryAdd(currency()) then
            undoCashAdds(inv, added)
            return false
        end
    end
    markDirty(inv)
    return true
end

function PhoneShop.payCashOnly(player, price)
    price = math.floor(tonumber(price) or 0)
    if price <= 0 then return true end
    player = PhoneShop.resolvePlayer(player)
    local money = collectMoney(player)
    local total = 0
    for _, e in ipairs(money) do
        total = total + e.worth
    end
    if total < price then return false end
    local inv = getInv(player)
    local ok, change, spent = payEntries(money, price)
    if not ok then return false end
    markDirty(inv)
    if change <= 0 then
        return true
    end
    if PhoneShop.giveCashOnly(player, change) then
        return true
    end
    PhoneShop.giveCashOnly(player, spent)
    return false
end

function PhoneShop.getMoney(player)
    player = PhoneShop.resolvePlayer(player)
    if not player then
        return 0
    end
    if PhoneShop.economyRules() and IKST_EconomyBridge and IKST_EconomyBridge.getBalance then
        return IKST_EconomyBridge.getBalance(player) or 0
    end
    return PhoneShop.getCashOnly(player)
end

function PhoneShop.canAfford(player, price)
    price = tonumber(price) or 0
    player = PhoneShop.resolvePlayer(player)
    if not player then
        return false
    end
    if PhoneShop.economyRules() and IKST_EconomyBridge and IKST_EconomyBridge.canAfford then
        return IKST_EconomyBridge.canAfford(player, price)
    end
    return PhoneShop.getCashOnly(player) >= price
end

function PhoneShop.pay(player, price)
    player = PhoneShop.resolvePlayer(player)
    if not player then
        return false
    end
    if PhoneShop.economyRules() and IKST_EconomyBridge and IKST_EconomyBridge.pay then
        local ok = IKST_EconomyBridge.pay(player, price)
        return ok == true
    end
    return PhoneShop.payCashOnly(player, price)
end

local function economyUsesBankOnly()
    if not PhoneShop.economyRules() or not IKST_Economy or not IKST_Economy.idCardBanking then
        return false
    end
    return IKST_Economy.idCardBanking() == true
end

-- How a successful pay() would split between cash items and bank (for symmetric refunds).
function PhoneShop.plannedPayment(player, price)
    price = math.floor(tonumber(price) or 0)
    if price <= 0 then
        return 0, 0
    end
    player = PhoneShop.resolvePlayer(player)
    if not player then
        return 0, 0
    end
    if not PhoneShop.economyRules() or not IKST_EconomyBridge then
        return price, 0
    end
    if economyUsesBankOnly() then
        return 0, price
    end
    local cash = IKST_EconomyBridge.getCash(player)
    if cash >= price then
        return price, 0
    end
    if IKST_Economy and IKST_Economy.getBank then
        return cash, price - cash
    end
    return price, 0
end

function PhoneShop.refundPayment(player, fromCash, fromBank)
    player = PhoneShop.resolvePlayer(player)
    if not player then
        return false
    end
    fromCash = math.floor(tonumber(fromCash) or 0)
    fromBank = math.floor(tonumber(fromBank) or 0)
    if fromCash <= 0 and fromBank <= 0 then
        return true
    end
    local ok = true
    if fromBank > 0 and IKST_EconomyBridge and IKST_EconomyBridge.giveBank then
        ok = IKST_EconomyBridge.giveBank(player, fromBank) == true
    end
    if ok and fromCash > 0 then
        if PhoneShop.economyRules() and IKST_EconomyBridge and IKST_EconomyBridge.giveCash then
            ok = IKST_EconomyBridge.giveCash(player, fromCash) == true
        else
            ok = PhoneShop.giveCashOnly(player, fromCash)
        end
    end
    return ok
end

function PhoneShop.give(player, amount)
    amount = math.floor(tonumber(amount) or 0)
    if amount <= 0 then
        return true
    end
    player = PhoneShop.resolvePlayer(player)
    if not player then
        return false
    end
    if PhoneShop.economyRules() and IKST_EconomyBridge and IKST_EconomyBridge.giveCash then
        return IKST_EconomyBridge.giveCash(player, amount) == true
    end
    return PhoneShop.giveCashOnly(player, amount)
end

function PhoneShop.findItem(player, itemType)
    local inv = getInv(player)
    if not inv or not itemType then return nil, nil end
    local item = inv:getItemFromTypeRecurse(itemType)
    if not item then return nil, nil end
    return item:getContainer() or inv, item
end

function PhoneShop.hasItem(player, itemType)
    return PhoneShop.findItem(player, itemType) ~= nil
end

local function tradeResult(success, msg, player)
    return { success = success, msg = msg, balance = PhoneShop.getMoney(player) }
end

function PhoneShop.trade(player, command, args, opts)
    opts = opts or {}
    local skipLog = opts.skipLog == true
    player = PhoneShop.resolvePlayer(player)
    if not player then
        return { success = false, msg = "No player.", balance = 0 }
    end
    if not PhoneShop.runsOnAuthorityJvm() then
        return tradeResult(false, "Server only.", player)
    end
    local itemType = args and args.itemType
    if type(itemType) ~= "string" or itemType == "" or #itemType > 256 then
        return tradeResult(false, "Invalid item.", player)
    end

    if command == PhoneShop.CMD.BUY then
        local entry = PhoneShopConfig.BuyByType[itemType]
        if not entry then
            return tradeResult(false, "Item not in shop.", player)
        end
        if PhoneShopConfig.ValidateItemsOnTrade ~= false then
            local ok, reason = PhoneShop.isShopItemAvailable(itemType, entry)
            if not ok then
                return tradeResult(false, reason or "Item not available.", player)
            end
        end
        if not PhoneShop.canAfford(player, entry.price) then
            return tradeResult(false, "Not enough money.", player)
        end
        local refundCash, refundBank = PhoneShop.plannedPayment(player, entry.price)
        if not PhoneShop.pay(player, entry.price) then
            return tradeResult(false, "Payment failed.", player)
        end
        if PhoneShop.isPinkSlipItemType(itemType) then
            local ok, err = PhoneShopPinkSlip.mint(player, entry)
            if not ok then
                PhoneShop.refundPayment(player, refundCash, refundBank)
                PhoneShop.logTradeFailed(player, command, itemType, tostring(err or "mint failed"))
                return tradeResult(false, tostring(err or "Could not issue Pink Slip."), player)
            end
        elseif not addItem(getInv(player), entry.itemType) then
            PhoneShop.refundPayment(player, refundCash, refundBank)
            PhoneShop.logTradeFailed(player, command, itemType, "Could not add item.")
            return tradeResult(false, "Inventory full or item unavailable — payment refunded.", player)
        end
        if not skipLog then
            PhoneShop.logTrade(player, command, entry)
        end
        return tradeResult(true, "Bought " .. entry.label .. " for $" .. entry.price .. ".", player), entry

    elseif command == PhoneShop.CMD.SELL then
        local entry = PhoneShopConfig.SellByType[itemType]
        if not entry then
            PhoneShop.logTradeFailed(player, command, itemType, "Cannot sell that here.")
            return tradeResult(false, "Cannot sell that here.", player)
        end
        local foundInv, foundItem = PhoneShop.findItem(player, itemType)
        if not foundInv then
            PhoneShop.logTradeFailed(player, command, itemType, "Item not in inventory.")
            return tradeResult(false, "You don't have " .. entry.label .. ".", player)
        end
        removeItem(foundInv, foundItem)
        markDirty(getInv(player))
        if not PhoneShop.give(player, entry.price) then
            addItem(getInv(player), entry.itemType)
            markDirty(getInv(player))
            PhoneShop.logTradeFailed(player, command, itemType, "Payout failed.")
            return tradeResult(false, "Payment failed.", player)
        end
        if not skipLog then
            PhoneShop.logTrade(player, command, entry)
        end
        return tradeResult(true, "Sold " .. entry.label .. " for $" .. entry.price .. ".", player), entry
    end

    return tradeResult(false, "Unknown action.", player)
end
