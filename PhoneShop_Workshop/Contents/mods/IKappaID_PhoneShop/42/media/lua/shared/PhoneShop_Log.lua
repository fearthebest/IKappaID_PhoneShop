-- PhoneShop — server-admin trade logs (per dedicated server world / SP save)

require "PhoneShop_Shared"
require "PhoneShop_Config"

PhoneShopLog = PhoneShopLog or {}
PhoneShopLog.stats = PhoneShopLog.stats or { buy = {}, sell = {} }
PhoneShopLog.players = PhoneShopLog.players or {}
PhoneShopLog.totals = PhoneShopLog.totals or { buyCount = 0, buyValue = 0, sellCount = 0, sellValue = 0 }
PhoneShopLog.recent = PhoneShopLog.recent or {}
PhoneShopLog.loaded = false
PhoneShopLog.tradeSeq = PhoneShopLog.tradeSeq or 0
PhoneShopLog.headersDone = PhoneShopLog.headersDone or {}
PhoneShopLog.readmeDone = PhoneShopLog.readmeDone or false
PhoneShopLog.serverLogged = PhoneShopLog.serverLogged or false

local TRADE_HEADER = "seq\tgame_time\tworld_hour\tplayer\taction\titem_type\tlabel\tcategory\tprice"
local STATS_HEADER = "action\titem_type\tlabel\tcategory\tcount\ttotal_value"
local PLAYER_HEADER = "player\tbuy_count\tbuy_spent\tsell_count\tsell_earned\ttotal_trades"

local function logEnabled()
    return PhoneShopConfig.LogEnabled ~= false
end

local function logRoot()
    local folder = PhoneShopConfig.LogFolder or "IKappaID_PhoneShop_Logs"
    if type(folder) ~= "string" or folder == "" then
        return "IKappaID_PhoneShop_Logs"
    end
    return folder
end

local function recentLimit()
    local n = tonumber(PhoneShopConfig.LogRecentCount)
    if not n or n < 5 then return 30 end
    return math.min(n, 200)
end

local function useSandbox()
    if PhoneShopConfig.LogUseSandbox == false then return false end
    return getSandboxFileWriter ~= nil and getSandboxFileReader ~= nil
end

local function isServerLogger()
    if not logEnabled() then return false end
    if not getFileWriter and not getSandboxFileWriter then return false end
    if isMultiplayer() then
        return type(isServer) == "function" and isServer()
    end
    return type(isClient) == "function" and isClient()
end

local function relPath(...)
    local parts = { logRoot() }
    for i = 1, select("#", ...) do
        table.insert(parts, select(i, ...))
    end
    return table.concat(parts, "/")
end

local function openReader(path)
    if useSandbox() then
        local reader = getSandboxFileReader(path, false)
        if reader then return reader end
    end
    if getFileReader then
        return getFileReader(path, false)
    end
    return nil
end

local function openWriter(path, append)
    if useSandbox() then
        local writer = getSandboxFileWriter(path, true, append)
        if writer then return writer end
    end
    if getFileWriter then
        return getFileWriter(path, true, append)
    end
    return nil
end

local function writeText(path, text, append)
    local writer = openWriter(path, append)
    if not writer then return false end
    if writer.writeln then
        writer:writeln(text)
    else
        writer:write(text .. "\r\n")
    end
    writer:close()
    return true
end

local function writeLines(path, lines)
    local writer = openWriter(path, false)
    if not writer then return false end
    for _, line in ipairs(lines) do
        if writer.writeln then
            writer:writeln(line)
        else
            writer:write(line .. "\r\n")
        end
    end
    writer:close()
    return true
end

local function fileExists(path)
    local reader = openReader(path)
    if not reader then return false end
    reader:close()
    return true
end

local function ensureHeader(path, header)
    if PhoneShopLog.headersDone[path] then return end
    if fileExists(path) then
        PhoneShopLog.headersDone[path] = true
        return
    end
    writeText(path, header, false)
    PhoneShopLog.headersDone[path] = true
end

local function playerName(player)
    if not player then return "unknown" end
    if player.getUsername then
        local name = player:getUsername()
        if name and name ~= "" then return name end
    end
    if player.getDescriptor then
        local desc = player:getDescriptor()
        if desc and desc.getForename and desc.getSurname then
            local first = desc:getForename() or ""
            local last = desc:getSurname() or ""
            local full = (first .. " " .. last):match("^%s*(.-)%s*$")
            if full and full ~= "" then return full end
        end
    end
    return "local"
end

local function gameDateParts()
    local gt = getGameTime and getGameTime()
    if not gt then return nil end
    return {
        year = gt.getYear and gt:getYear() or 0,
        month = gt.getMonth and (gt:getMonth() + 1) or 0,
        day = gt.getDay and (gt:getDay() + 1) or 0,
        hours = gt.getWorldAgeHours and gt:getWorldAgeHours() or 0,
    }
end

local function dateFolder()
    local p = gameDateParts()
    if not p then return "undated" end
    return string.format("%04d-%02d-%02d", p.year, p.month, p.day)
end

local function gameTimeTag()
    local p = gameDateParts()
    if not p then return "?", 0 end
    return string.format("Y%04d-%02d-%02d H%.1f", p.year, p.month, p.day, p.hours), p.hours
end

local function bucketKey(action)
    if action == PhoneShop.CMD.BUY or action == "buy" or action == "BUY" then return "buy" end
    return "sell"
end

local function ensurePlayerRow(name)
    local row = PhoneShopLog.players[name]
    if not row then
        row = { buyCount = 0, buySpent = 0, sellCount = 0, sellEarned = 0 }
        PhoneShopLog.players[name] = row
    end
    return row
end

local function parseStatsLine(line)
    if not line or line == "" or line:sub(1, 1) == "#" then return end
    local action, itemType, label, category, count, total

    if line:find("\t", 1, true) then
        action, itemType, label, category, count, total = line:match(
            "^([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t(%d+)\t(%d+)$"
        )
    else
        action, itemType, label, category, count, total = line:match(
            "^([^|]+)|([^|]+)|([^|]+)|([^|]+)|(%d+)|(%d+)$"
        )
    end

    count = tonumber(count)
    total = tonumber(total)
    if not action or not itemType or not count or not total then return end

    local bucket = bucketKey(action)
    PhoneShopLog.stats[bucket][itemType] = {
        itemType = itemType,
        label = label or itemType,
        category = category or "",
        count = count,
        total = total,
    }
    if bucket == "buy" then
        PhoneShopLog.totals.buyCount = PhoneShopLog.totals.buyCount + count
        PhoneShopLog.totals.buyValue = PhoneShopLog.totals.buyValue + total
    else
        PhoneShopLog.totals.sellCount = PhoneShopLog.totals.sellCount + count
        PhoneShopLog.totals.sellValue = PhoneShopLog.totals.sellValue + total
    end
end

local function parsePlayerLine(line)
    if not line or line == "" or line:find("player", 1, true) == 1 then return end
    local name, buyCount, buySpent, sellCount, sellEarned = line:match(
        "^([^\t]+)\t(%d+)\t(%d+)\t(%d+)\t(%d+)\t(%d+)$"
    )
    buyCount = tonumber(buyCount)
    buySpent = tonumber(buySpent)
    sellCount = tonumber(sellCount)
    sellEarned = tonumber(sellEarned)
    if not name or not buyCount then return end
    PhoneShopLog.players[name] = {
        buyCount = buyCount,
        buySpent = buySpent,
        sellCount = sellCount,
        sellEarned = sellEarned,
    }
end

local function loadMeta()
    local reader = openReader(relPath("stats", "meta.txt"))
    if not reader then return end
    while true do
        local line = reader:readLine()
        if not line then break end
        local key, val = line:match("^(%w+)=(.+)$")
        if key == "trade_seq" then
            PhoneShopLog.tradeSeq = tonumber(val) or PhoneShopLog.tradeSeq
        end
    end
    reader:close()
end

local function loadStatsFile(path)
    local reader = openReader(path)
    if not reader then return end
    local first = true
    while true do
        local line = reader:readLine()
        if not line or line == "" then break end
        if first and line:find("action", 1, true) and line:find("item_type", 1, true) then
            first = false
        else
            parseStatsLine(line)
        end
    end
    reader:close()
end

local function loadPlayersFile()
    local reader = openReader(relPath("stats", "by_player.tsv"))
    if not reader then return end
    while true do
        local line = reader:readLine()
        if not line or line == "" then break end
        parsePlayerLine(line)
    end
    reader:close()
end

local function loadRecentFile()
    PhoneShopLog.recent = {}
    local reader = openReader(relPath("stats", "recent_trades.txt"))
    if not reader then return end
    while true do
        local line = reader:readLine()
        if not line or line == "" then break end
        if line:find("seq", 1, true) ~= 1 then
            table.insert(PhoneShopLog.recent, line)
        end
    end
    reader:close()
end

local function ensureLoaded()
    if PhoneShopLog.loaded then return end
    PhoneShopLog.loaded = true
    PhoneShopLog.stats = { buy = {}, sell = {} }
    PhoneShopLog.players = {}
    PhoneShopLog.totals = { buyCount = 0, buyValue = 0, sellCount = 0, sellValue = 0 }

    loadMeta()
    loadStatsFile(relPath("stats", "by_item.tsv"))
    if PhoneShopLog.totals.buyCount == 0 and PhoneShopLog.totals.sellCount == 0 then
        loadStatsFile(relPath("stats_data.txt"))
    end
    loadPlayersFile()
    loadRecentFile()
end

local function ensureReadme()
    if PhoneShopLog.readmeDone then return end
    local path = relPath("README.txt")
    if fileExists(path) then
        PhoneShopLog.readmeDone = true
        return
    end
    local lines = {
        "IKappaID Phone Shop — SERVER ADMIN LOGS",
        "========================================",
        "",
        "Dedicated server: inside THIS world save folder:",
        "  Zomboid/Saves/Multiplayer/<ServerName>/IKappaID_PhoneShop_Logs/",
        "",
        ">>> START HERE: open ADMIN.txt <<<",
        "",
        "ADMIN.txt              — one-page server dashboard (updated every trade)",
        "stats/by_player.tsv    — per-player totals (Excel)",
        "stats/by_item.tsv      — per-item totals (Excel)",
        "stats/recent_trades.txt— last trades audit tail",
        "trades/YYYY-MM-DD/     — full daily buy/sell/all logs (TSV)",
        "server/server.log      — server start / mod ready events",
        "",
        "Config: media/lua/shared/PhoneShop_Config.lua",
        "",
    }
    writeLines(path, lines)
    PhoneShopLog.readmeDone = true
end

local function saveMeta()
    writeLines(relPath("stats", "meta.txt"), {
        "trade_seq=" .. tostring(PhoneShopLog.tradeSeq),
    })
end

local function updatePlayerStats(player, command, price)
    local name = playerName(player)
    local row = ensurePlayerRow(name)
    if bucketKey(command) == "buy" then
        row.buyCount = row.buyCount + 1
        row.buySpent = row.buySpent + price
    else
        row.sellCount = row.sellCount + 1
        row.sellEarned = row.sellEarned + price
    end
end

local function updateStats(action, entry)
    ensureLoaded()
    local bucket = bucketKey(action)
    local stats = PhoneShopLog.stats[bucket]
    local row = stats[entry.itemType]
    if not row then
        row = {
            itemType = entry.itemType,
            label = entry.label,
            category = entry.category,
            count = 0,
            total = 0,
        }
        stats[entry.itemType] = row
    end
    row.label = entry.label
    row.category = entry.category
    row.count = row.count + 1
    row.total = row.total + entry.price

    if bucket == "buy" then
        PhoneShopLog.totals.buyCount = PhoneShopLog.totals.buyCount + 1
        PhoneShopLog.totals.buyValue = PhoneShopLog.totals.buyValue + entry.price
    else
        PhoneShopLog.totals.sellCount = PhoneShopLog.totals.sellCount + 1
        PhoneShopLog.totals.sellValue = PhoneShopLog.totals.sellValue + entry.price
    end
end

local function sortedRows(bucket, sortBy)
    local rows = {}
    for _, row in pairs(PhoneShopLog.stats[bucket]) do
        table.insert(rows, row)
    end
    if sortBy == "total" then
        table.sort(rows, function(a, b)
            if a.total ~= b.total then return a.total > b.total end
            if a.count ~= b.count then return a.count > b.count end
            return a.label < b.label
        end)
    else
        table.sort(rows, function(a, b)
            if a.count ~= b.count then return a.count > b.count end
            if a.total ~= b.total then return a.total > b.total end
            return a.label < b.label
        end)
    end
    return rows
end

local function sortedPlayers()
    local rows = {}
    for name, row in pairs(PhoneShopLog.players) do
        local totalTrades = row.buyCount + row.sellCount
        table.insert(rows, {
            name = name,
            buyCount = row.buyCount,
            buySpent = row.buySpent,
            sellCount = row.sellCount,
            sellEarned = row.sellEarned,
            totalTrades = totalTrades,
        })
    end
    table.sort(rows, function(a, b)
        if a.totalTrades ~= b.totalTrades then return a.totalTrades > b.totalTrades end
        return a.name < b.name
    end)
    return rows
end

local function pushRecent(line)
    table.insert(PhoneShopLog.recent, line)
    local limit = recentLimit()
    while #PhoneShopLog.recent > limit do
        table.remove(PhoneShopLog.recent, 1)
    end
end

local function savePlayerStats()
    local lines = { PLAYER_HEADER }
    for _, row in ipairs(sortedPlayers()) do
        table.insert(lines, string.format(
            "%s\t%d\t%d\t%d\t%d\t%d",
            row.name, row.buyCount, row.buySpent, row.sellCount, row.sellEarned, row.totalTrades
        ))
    end
    writeLines(relPath("stats", "by_player.tsv"), lines)
end

local function saveRecentTrades()
    local lines = { TRADE_HEADER }
    for _, line in ipairs(PhoneShopLog.recent) do
        table.insert(lines, line)
    end
    writeLines(relPath("stats", "recent_trades.txt"), lines)
end

local function saveAdminDashboard(lastLine)
    ensureLoaded()
    local timeStr = gameTimeTag()
    local lines = {
        "IKappaID Phone Shop — SERVER ADMIN DASHBOARD",
        "============================================",
        "Updated: " .. timeStr,
        "Last trade: " .. (lastLine or "(none)"),
        "",
        "QUICK TOTALS",
        string.format("  Purchases: %d trades | $%d spent by players", PhoneShopLog.totals.buyCount, PhoneShopLog.totals.buyValue),
        string.format("  Sales:     %d trades | $%d paid to players", PhoneShopLog.totals.sellCount, PhoneShopLog.totals.sellValue),
        string.format("  Net shop flow: $%d in  -  $%d out", PhoneShopLog.totals.buyValue, PhoneShopLog.totals.sellValue),
        "",
        "TOP PLAYERS (by trade count)",
    }

    local players = sortedPlayers()
    if #players == 0 then
        table.insert(lines, "  (no trades yet)")
    else
        for i = 1, math.min(15, #players) do
            local p = players[i]
            table.insert(lines, string.format(
                "  %2d. %s — %d trades | bought $%d | sold $%d",
                i, p.name, p.totalTrades, p.buySpent, p.sellEarned
            ))
        end
    end

    table.insert(lines, "")
    table.insert(lines, "TOP SOLD ITEMS")
    local sold = sortedRows("sell", "count")
    if #sold == 0 then
        table.insert(lines, "  (none)")
    else
        for i = 1, math.min(10, #sold) do
            local r = sold[i]
            table.insert(lines, string.format("  %2d. %s x%d ($%d) [%s]", i, r.label, r.count, r.total, r.category))
        end
    end

    table.insert(lines, "")
    table.insert(lines, "TOP BOUGHT ITEMS")
    local bought = sortedRows("buy", "count")
    if #bought == 0 then
        table.insert(lines, "  (none)")
    else
        for i = 1, math.min(10, #bought) do
            local r = bought[i]
            table.insert(lines, string.format("  %2d. %s x%d ($%d) [%s]", i, r.label, r.count, r.total, r.category))
        end
    end

    table.insert(lines, "")
    table.insert(lines, "RECENT TRADES (newest last — see recent_trades.txt for TSV)")
    local n = #PhoneShopLog.recent
    if n == 0 then
        table.insert(lines, "  (none)")
    else
        local start = math.max(1, n - 14)
        for i = start, n do
            table.insert(lines, "  " .. PhoneShopLog.recent[i]:gsub("\t", " | "))
        end
    end

    table.insert(lines, "")
    table.insert(lines, "ADMIN FILES")
    table.insert(lines, "  ADMIN.txt              (this file)")
    table.insert(lines, "  stats/by_player.tsv    — player breakdown")
    table.insert(lines, "  stats/by_item.tsv      — item breakdown")
    table.insert(lines, "  stats/recent_trades.txt— audit tail")
    table.insert(lines, "  trades/" .. dateFolder() .. "/all.txt — today's full log")
    table.insert(lines, "  server/server.log      — server sessions")
    table.insert(lines, "")
    table.insert(lines, "TROUBLESHOOTING")
    table.insert(lines, "  No folder? Enable LogEnabled in PhoneShop_Config.lua and restart server.")
    table.insert(lines, "  Wrong world? Each save has its own IKappaID_PhoneShop_Logs folder.")
    table.insert(lines, "  Edit shop lists: media/phoneshop/buy_list.txt, sell_list.txt, vehicle_list.txt, costume_list.txt")

    writeLines(relPath("ADMIN.txt"), lines)
end

local function saveStatsFiles(lastLine)
    ensureLoaded()

    local itemLines = { STATS_HEADER }
    for _, bucket in ipairs({ "buy", "sell" }) do
        local action = bucket == "buy" and "BUY" or "SELL"
        for _, row in ipairs(sortedRows(bucket, "count")) do
            table.insert(itemLines, string.format(
                "%s\t%s\t%s\t%s\t%d\t%d",
                action, row.itemType, row.label, row.category, row.count, row.total
            ))
        end
    end
    writeLines(relPath("stats", "by_item.tsv"), itemLines)
    savePlayerStats()
    saveRecentTrades()
    saveMeta()

    writeLines(relPath("stats", "summary.txt"), {
        "See ADMIN.txt for the server dashboard.",
        "Last trade: " .. (lastLine or ""),
        string.format("Purchases: %d ($%d)", PhoneShopLog.totals.buyCount, PhoneShopLog.totals.buyValue),
        string.format("Sales: %d ($%d)", PhoneShopLog.totals.sellCount, PhoneShopLog.totals.sellValue),
    })

    saveAdminDashboard(lastLine)
end

local function appendTradeLine(dayPath, fileName, line)
    local path = relPath("trades", dayPath, fileName)
    ensureHeader(path, TRADE_HEADER)
    writeText(path, line, true)
end

local function buildTradeLine(player, action, entry)
    PhoneShopLog.tradeSeq = PhoneShopLog.tradeSeq + 1
    local timeStr, worldH = gameTimeTag()
    return string.format(
        "%06d\t%s\t%.1f\t%s\t%s\t%s\t%s\t%s\t%d",
        PhoneShopLog.tradeSeq, timeStr, worldH, playerName(player), action,
        entry.itemType, entry.label, entry.category, entry.price
    )
end

function PhoneShop.logServerReady()
    if not isServerLogger() or PhoneShopLog.serverLogged then return end
    PhoneShopLog.serverLogged = true
    ensureReadme()
    ensureLoaded()

    local timeStr = gameTimeTag()
    local mode = isMultiplayer() and "multiplayer-dedicated" or "singleplayer"
    local line = string.format("[%s] Phone Shop logging active | mode=%s | folder=%s", timeStr, mode, logRoot())
    ensureHeader(relPath("server", "server.log"), "timestamp\tevent")
    writeText(relPath("server", "server.log"), timeStr .. "\t" .. line, true)
    saveAdminDashboard("(server started — waiting for first trade)")
end

function PhoneShop.logTrade(player, command, entry)
    if not isServerLogger() or not entry then return end

    ensureReadme()
    if not PhoneShopLog.serverLogged then
        PhoneShop.logServerReady()
    end

    local action = command == PhoneShop.CMD.BUY and "BUY" or "SELL"
    local line = buildTradeLine(player, action, entry)
    local day = dateFolder()

    appendTradeLine(day, "all.txt", line)
    if action == "BUY" then
        appendTradeLine(day, "buys.txt", line)
    else
        appendTradeLine(day, "sells.txt", line)
    end

    pushRecent(line)
    updatePlayerStats(player, command, entry.price)
    updateStats(command, entry)
    saveStatsFiles(line)
end

function PhoneShop.logTradeFailed(player, command, itemType, reason)
    if not isServerLogger() or PhoneShopConfig.LogFailedTrades ~= true then return end

    ensureReadme()
    PhoneShopLog.tradeSeq = PhoneShopLog.tradeSeq + 1
    local timeStr, worldH = gameTimeTag()
    local action = command == PhoneShop.CMD.BUY and "BUY" or "SELL"
    local line = string.format(
        "%06d\t%s\t%.1f\t%s\tFAILED_%s\t%s\t%s",
        PhoneShopLog.tradeSeq, timeStr, worldH, playerName(player), action,
        itemType or "?", reason or "unknown"
    )
    local note = relPath("trades", dateFolder(), "failed.txt")
    ensureHeader(note, "seq\tgame_time\tworld_hour\tplayer\taction\titem_type\treason")
    writeText(note, line, true)
    pushRecent(line)
    saveRecentTrades()
    saveMeta()
end
