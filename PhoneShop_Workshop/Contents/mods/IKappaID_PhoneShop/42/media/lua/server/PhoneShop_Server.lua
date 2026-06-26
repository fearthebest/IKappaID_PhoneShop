-- PhoneShop — server (multiplayer)

if isClient() then return end

require "PhoneShop_Shared"
require "PhoneShop_Money"
require "PhoneShop_Log"

local lastTrade = {}

local function onClientCommand(module, command, player, args)
    if module ~= PhoneShop.MODULE or not player then return end

    if command == PhoneShop.CMD.GET_LIST_INFO then
        if PhoneShop.reloadShopLists then
            PhoneShop.reloadShopLists()
        end
        sendServerCommand(player, PhoneShop.MODULE, PhoneShop.CMD.LIST_INFO, PhoneShop.getListInfo())
        return
    end

    if command ~= PhoneShop.CMD.BUY and command ~= PhoneShop.CMD.SELL then return end

    local name = player:getUsername()
    local now = getTimeInMillis()
    if now - (lastTrade[name] or 0) < 500 then
        sendServerCommand(player, PhoneShop.MODULE, PhoneShop.CMD.RESULT, {
            success = false, msg = "Wait a moment.", balance = PhoneShop.getMoney(player),
        })
        return
    end
    lastTrade[name] = now

    sendServerCommand(player, PhoneShop.MODULE, PhoneShop.CMD.RESULT,
        PhoneShop.trade(player, command, args))
end

if Events and Events.OnClientCommand then
    Events.OnClientCommand.Add(onClientCommand)
end

local function onServerStarted()
    if PhoneShop.reloadShopLists then
        PhoneShop.reloadShopLists()
    end
    PhoneShop.logServerReady()
end

if Events and Events.OnServerStarted then
    Events.OnServerStarted.Add(onServerStarted)
end
