-- PhoneShop — server (multiplayer authority)

if type(isClient) == "function" and isClient()
    and type(isServer) == "function" and not isServer() then
    return
end

require "PhoneShop_Shared"
require "PhoneShop_Money"
require "PhoneShop_Log"

local RATE_TRADE_MS = 500
local RATE_LIST_MS = 1000

local lastTrade = {}
local lastListInfo = {}

local function playerKey(player)
    if not player or type(player.getUsername) ~= "function" then
        return nil
    end
    local name = player:getUsername()
    if type(name) ~= "string" or name == "" then
        return nil
    end
    return name
end

local function sendResult(player, result)
    if not result or type(result) ~= "table" then
        result = {
            success = false,
            msg = "Trade failed.",
            balance = PhoneShop.getMoney(player),
        }
    end
    if result.balance == nil then
        result.balance = PhoneShop.getMoney(player)
    end
    sendServerCommand(player, PhoneShop.MODULE, PhoneShop.CMD.RESULT, result)
end

local function sendListInfo(player)
    local info = PhoneShop.getListInfo()
    info.balance = PhoneShop.getMoney(player)
    sendServerCommand(player, PhoneShop.MODULE, PhoneShop.CMD.LIST_INFO, info)
end

local function validateTradeArgs(args)
    if type(args) ~= "table" then
        return nil
    end
    local itemType = args.itemType
    if type(itemType) ~= "string" or itemType == "" or #itemType > 256 then
        return nil
    end
    return { itemType = itemType }
end

local function handleGetListInfo(player)
    local name = playerKey(player)
    if not name then
        return
    end
    local now = getTimeInMillis()
    if now - (lastListInfo[name] or 0) < RATE_LIST_MS then
        -- Still reply so the client balance syncs (wiki: server pushes plain data).
        sendListInfo(player)
        return
    end
    lastListInfo[name] = now
    sendListInfo(player)
end

local function handleTrade(player, command, args)
    local name = playerKey(player)
    if not name then
        sendResult(player, { success = false, msg = "Invalid player.", balance = 0 })
        return
    end
    local safeArgs = validateTradeArgs(args)
    if not safeArgs then
        sendResult(player, {
            success = false,
            msg = "Invalid item.",
            balance = PhoneShop.getMoney(player),
        })
        return
    end
    local now = getTimeInMillis()
    if now - (lastTrade[name] or 0) < RATE_TRADE_MS then
        sendResult(player, {
            success = false, msg = "Wait a moment.", balance = PhoneShop.getMoney(player),
        })
        return
    end
    lastTrade[name] = now

    local result, logEntry = PhoneShop.trade(player, command, safeArgs, { skipLog = true })
    sendResult(player, result)
    if result and result.success and logEntry then
        PhoneShop.logTrade(player, command, logEntry)
    end
end

local COMMAND_HANDLERS = {
    [PhoneShop.CMD.GET_LIST_INFO] = handleGetListInfo,
    [PhoneShop.CMD.BUY] = function(player, args)
        handleTrade(player, PhoneShop.CMD.BUY, args)
    end,
    [PhoneShop.CMD.SELL] = function(player, args)
        handleTrade(player, PhoneShop.CMD.SELL, args)
    end,
}

local function onClientCommand(module, command, player, args)
    if module ~= PhoneShop.MODULE or not player then
        return
    end
    if type(isServer) == "function" and not isServer() then
        return
    end
    local handler = COMMAND_HANDLERS[command]
    if type(handler) ~= "function" then
        return
    end
    handler(player, args)
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
