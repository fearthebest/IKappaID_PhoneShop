-- PhoneShop — constants

PhoneShop = PhoneShop or {}

PhoneShop.MOD_ID = "IKappaID_PhoneShop"
PhoneShop.MODULE = PhoneShop.MOD_ID
PhoneShop.CMD = {
    BUY = "Buy",
    SELL = "Sell",
    RESULT = "Result",
    GET_LIST_INFO = "GetListInfo",
    LIST_INFO = "ListInfo",
}

PhoneShop.CURRENCY     = "Base.Money"
PhoneShop.BUNDLE       = "Base.MoneyBundle"
PhoneShop.BUNDLE_VALUE = 100

-- Synthetic buy key prefix for prefilled pink slips (see vehicle_list.txt).
PhoneShop.PINKSLIP_TAG = "@ps:"

function PhoneShop.isRemoteMpClient()
    return type(isClient) == "function" and isClient()
        and type(isServer) == "function" and not isServer()
        and type(isMultiplayer) == "function" and isMultiplayer()
end

function PhoneShop.resolvePlayer(playerOrNum)
    if playerOrNum == nil then
        return getPlayer and getPlayer() or nil
    end
    if type(playerOrNum) == "number" then
        if getSpecificPlayer then
            return getSpecificPlayer(playerOrNum)
        end
        return getPlayer and getPlayer() or nil
    end
    if playerOrNum.getInventory then
        return playerOrNum
    end
    return getPlayer and getPlayer() or nil
end

-- When IKST Economy addon is active, PhoneShop UI/trades use Economy for balances and payments.
-- Standalone PhoneShop ignores this and uses inventory cash only.
function PhoneShop.economyRules()
    if IKST_Economy and IKST_Economy.isEconomyActive then
        return IKST_Economy.isEconomyActive() == true
    end
    return false
end
