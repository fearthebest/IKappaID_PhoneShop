-- PhoneShop — client UI (dark theme)

if type(isServer) == "function" and isServer() and not isClient() then
    return
end

require "PhoneShop_Shared"
require "PhoneShop_Money"
require "PhoneShop_PinkSlip"
require "PhoneShop_TimedActions"
require "ISUI/ISPanel"
require "ISUI/ISButton"
require "ISUI/ISTextEntryBox"
require "ISUI/ISCollapsableWindow"

PhoneShopClient = PhoneShopClient or {}
PhoneShopClient.Window = nil
PhoneShopClient.TexCache = {}
PhoneShopClient.Balance = 0
PhoneShopClient.activePlayer = nil
PhoneShopClient.listMismatch = false
PhoneShopClient.balanceSynced = false

function PhoneShopClient.getPlayer()
    return PhoneShop.resolvePlayer(PhoneShopClient.activePlayer)
end

-- UI palette (0–1)
local C = {
    bg      = { r=0.10, g=0.10, b=0.10 },
    card    = { r=0.17, g=0.17, b=0.17 },
    chipOff = { r=0.24, g=0.24, b=0.24 },
    orange  = { r=1.00, g=0.40, b=0.00 },
    orangeD = { r=0.75, g=0.30, b=0.00 },
    white   = { r=0.95, g=0.95, b=0.95 },
    muted   = { r=0.54, g=0.54, b=0.54 },
    divider = { r=0.23, g=0.23, b=0.23 },
    sel     = { r=0.22, g=0.22, b=0.22 },
    danger  = { r=0.90, g=0.30, b=0.25 },
    ok      = { r=0.45, g=0.85, b=0.50 },
}

local PAD, ROW_H, ITEM_H, ICON_SZ = 14, 30, 30, 22
local WIN_W, WIN_H = 520, 580
local TAB_H, TAB_GAP, TAB_W = 24, 4, 86
local COL_ICON, COL_NAME, COL_PRICE = 6, ICON_SZ + 14, 350
local Y_BAL, Y_BS, Y_CAT = 30, 56, 94
local Y_SEARCH, Y_DIV = 178, 206
local Y_COLHDR, Y_LIST, Y_BTM = 212, 234, 76

local knownItems = {}
local filterCache = {}
local filterStats = {}

function PhoneShopClient.resetItemCaches()
    knownItems = {}
    filterCache = {}
    filterStats = {}
    PhoneShopClient.TexCache = {}
end

function PhoneShopClient.onServerListInfo(info)
    if not info then return end
    if info.balance ~= nil then
        PhoneShopClient.Balance = tonumber(info.balance) or 0
        PhoneShopClient.balanceSynced = true
    end
    if info.fingerprint then
        local localInfo = PhoneShop.getListInfo and PhoneShop.getListInfo() or nil
        if localInfo then
            PhoneShopClient.listMismatch = info.fingerprint ~= localInfo.fingerprint
        end
    end
    local win = PhoneShopClient.Window
    if win and win:isVisible() then
        win:applyFilter()
    end
end

local function col(c, a)
    return c.r, c.g, c.b, a or 1
end

local function btnStyle(bg)
    return {
        backgroundColor = { r=bg.r, g=bg.g, b=bg.b, a=1 },
        borderColor     = { r=bg.r, g=bg.g, b=bg.b, a=1 },
    }
end

local function applyBtnStyle(btn, bg)
    local s = btnStyle(bg)
    btn.backgroundColor = s.backgroundColor
    btn.borderColor = s.borderColor
end

local function refreshBalance(player)
    player = player or PhoneShopClient.getPlayer()
    PhoneShopClient.Balance = player and PhoneShop.getMoney(player) or 0
end

local function getItemIcon(itemType)
    if PhoneShopClient.TexCache[itemType] ~= nil then
        return PhoneShopClient.TexCache[itemType] or nil
    end
    local tex = nil
    local lookupType = itemType
    if PhoneShop.isPinkSlipItemType(itemType) then
        lookupType = "IKappaIDPinkSlip.PinkSlip"
    end
    local si = ScriptManager.instance:FindItem(lookupType)
    if si then
        local icon = si:getIcon()
        if icon and icon ~= "" then
            tex = getTexture("media/textures/Item_" .. icon .. ".png")
            if not tex then tex = getTexture("Item_" .. icon) end
        end
    end
    PhoneShopClient.TexCache[itemType] = tex or false
    return tex
end

local function isShopItemKnown(itemType)
    if PhoneShop.isPinkSlipItemType(itemType) then
        local slipType = "IKappaIDPinkSlip.PinkSlip"
        if ScriptManager.instance:FindItem(slipType) == nil then
            return false
        end
        local scriptName = PhoneShop.pinkSlipVehicleScript(itemType)
        return scriptName ~= nil and PhoneShop.vehicleScriptExists(scriptName)
    end
    return ScriptManager.instance:FindItem(itemType) ~= nil
end

local function filterList(srcKey, list, category)
    local rev = PhoneShop.listRevision or 0
    local key = rev .. "|" .. tostring(list) .. "|" .. srcKey .. "|" .. category
    if filterCache[key] then
        return filterCache[key], filterStats[key]
    end
    local out = {}
    local totalInCat = 0
    local hiddenByPrefix = {}
    for _, e in ipairs(list) do
        if category == "All" or e.category == category then
            totalInCat = totalInCat + 1
            if knownItems[e.itemType] == nil then
                knownItems[e.itemType] = isShopItemKnown(e.itemType)
            end
            if knownItems[e.itemType] then
                table.insert(out, e)
            else
                local prefix = e.itemType:match("^([^.]+)%.") or "?"
                hiddenByPrefix[prefix] = (hiddenByPrefix[prefix] or 0) + 1
            end
        end
    end
    local stats = { visible = #out, total = totalInCat, hiddenByPrefix = hiddenByPrefix }
    filterCache[key] = out
    filterStats[key] = stats
    return out, stats
end

local function matchesSearch(entry, query)
    if not query or query == "" then return true end
    query = string.lower(query)
    if string.find(string.lower(entry.label), query, 1, true) then return true end
    if string.find(string.lower(entry.itemType), query, 1, true) then return true end
    if string.find(string.lower(entry.category), query, 1, true) then return true end
    return false
end

local function showResult(result)
    local win = PhoneShopClient.Window
    if not win or not win:isVisible() or not result then return end
    if result.balance ~= nil then
        PhoneShopClient.Balance = tonumber(result.balance) or 0
        PhoneShopClient.balanceSynced = true
    elseif PhoneShop.isSinglePlayer() then
        refreshBalance()
        PhoneShopClient.balanceSynced = true
    end
    if result.success then
        win:setStatus(result.msg, C.ok.r, C.ok.g, C.ok.b)
    else
        win:setStatus(result.msg, C.danger.r, C.danger.g, C.danger.b)
    end
    win:applyFilter()
end

local function doTrade(command, itemType)
    local player = PhoneShopClient.getPlayer()
    if not player then return end
    local args = { itemType = itemType }
    -- PZwiki: MP inventory/money mutations on server (all MP clients, including host).
    if type(isMultiplayer) == "function" and isMultiplayer() then
        sendClientCommand(PhoneShop.MODULE, command, args)
    else
        showResult(PhoneShop.trade(player, command, args))
    end
end

PhoneShopList = ISPanel:derive("PhoneShopList")

function PhoneShopList:new(x, y, w, h)
    local o = ISPanel.new(self, x, y, w, h)
    o.backgroundColor = { r=C.card.r, g=C.card.g, b=C.card.b, a=1 }
    o.borderColor = { r=C.divider.r, g=C.divider.g, b=C.divider.b, a=1 }
    o.entries, o.selected, o.scrollY = {}, -1, 0
    o.checkAfford = true
    o.emptyText = "No items in this category."
    return o
end

function PhoneShopList:initialise() ISPanel.initialise(self) end

function PhoneShopList:setEntries(list, emptyText)
    local keep = self.selected
    self.entries = list or {}
    self.emptyText = emptyText or "No items found."
    self.selected = (keep >= 1 and keep <= #self.entries) and keep or -1
    self.scrollY = 0
end

function PhoneShopList:getSelected()
    if self.selected >= 1 and self.selected <= #self.entries then
        return self.entries[self.selected]
    end
end

function PhoneShopList:render()
    ISPanel.render(self)
    if #self.entries == 0 then
        self:drawText(self.emptyText, COL_NAME, 12, col(C.muted))
        return
    end
    local money = PhoneShopClient.Balance
    for i, entry in ipairs(self.entries) do
        local rowY = (i - 1) * ITEM_H - self.scrollY
        if rowY + ITEM_H > 0 and rowY < self.height then
            if self.selected == i then
                self:drawRect(0, rowY, self.width, ITEM_H, 1, col(C.sel))
            end
            if i < #self.entries then
                local lineY = rowY + ITEM_H - 1
                if lineY > 0 and lineY < self.height then
                    self:drawRect(0, lineY, self.width, 1, 1, col(C.divider))
                end
            end
            local tex = getItemIcon(entry.itemType)
            local iconY = rowY + math.floor((ITEM_H - ICON_SZ) / 2)
            if tex then
                self:drawTextureScaled(tex, COL_ICON, iconY, ICON_SZ, ICON_SZ, 1.0)
            end
            local nr, ng, nb = col(C.white)
            local pr, pg, pb = col(C.orange)
            if self.checkAfford and money < entry.price then
                nr, ng, nb = col(C.danger)
                pr, pg, pb = col(C.danger)
            end
            self:drawText(entry.label, COL_NAME, rowY + 7, nr, ng, nb, 1, UIFont.Small)
            self:drawText("$" .. entry.price, COL_PRICE, rowY + 7, pr, pg, pb, 1, UIFont.Small)
        end
    end
end

function PhoneShopList:onMouseWheel(del)
    local max = math.max(0, #self.entries * ITEM_H - self.height)
    self.scrollY = math.max(0, math.min(self.scrollY + del * ITEM_H * 2, max))
    return true
end

function PhoneShopList:onMouseDown(x, y)
    local idx = math.floor((y + self.scrollY) / ITEM_H) + 1
    if idx >= 1 and idx <= #self.entries then
        self.selected = idx
        if self.onSelect then self.onSelect(self.entries[idx]) end
    end
end

PhoneShopUI = ISCollapsableWindow:derive("PhoneShopUI")

function PhoneShopUI:new(x, y, w, h)
    local o = ISCollapsableWindow.new(self, x, y, w, h)
    o.title = "IKappaID Phone Shop"
    o.resizable = false
    o.backgroundColor = { r=C.bg.r, g=C.bg.g, b=C.bg.b, a=1 }
    o.borderColor = { r=C.divider.r, g=C.divider.g, b=C.divider.b, a=1 }
    o.mode = "buy"
    o.activeCat = "All"
    o.searchText = ""
    o.showAffordableOnly = false
    o.listHint = ""
    o.statusText = "Select an item, then press the action button."
    o.statusR, o.statusG, o.statusB = C.muted.r, C.muted.g, C.muted.b
    o:setWantKeyEvents(true)
    return o
end

function PhoneShopUI:initialise()
    ISCollapsableWindow.initialise(self)
    self:buildUI()
end

function PhoneShopUI:buildUI()
    local cw, ch = self.width, self.height
    local segW = math.floor((cw - PAD * 2 - 4) / 2)

    self.btnBuy = ISButton:new(PAD, Y_BS, segW, ROW_H, "BUY", self, PhoneShopUI.switchBuy)
    self.btnSell = ISButton:new(PAD + segW + 4, Y_BS, segW, ROW_H, "SELL", self, PhoneShopUI.switchSell)
    self.btnBuy:initialise(); self:addChild(self.btnBuy)
    self.btnSell:initialise(); self:addChild(self.btnSell)

    self.catBtns = {}
    local cats = { "All" }
    for _, c in ipairs(PhoneShopConfig.Categories) do table.insert(cats, c) end
    for i, cat in ipairs(cats) do
        local colIdx, row = (i - 1) % 5, math.floor((i - 1) / 5)
        local btn = ISButton:new(PAD + colIdx * (TAB_W + TAB_GAP), Y_CAT + row * (TAB_H + TAB_GAP),
            TAB_W, TAB_H, cat, self, PhoneShopUI.onCatClick)
        btn.catName = cat
        btn:initialise()
        self:addChild(btn)
        table.insert(self.catBtns, btn)
    end

    local searchW = cw - PAD * 2 - 98
    self.searchEntry = ISTextEntryBox:new("", PAD, Y_SEARCH, searchW, 24)
    self.searchEntry:initialise()
    self.searchEntry:instantiate()
    self.searchEntry.backgroundColor = { r=C.card.r, g=C.card.g, b=C.card.b, a=1 }
    self.searchEntry.borderColor = { r=C.divider.r, g=C.divider.g, b=C.divider.b, a=1 }
    self.searchEntry.onTextChange = function()
        self.searchText = self.searchEntry:getText() or ""
        self:applyFilter()
    end
    self:addChild(self.searchEntry)

    self.btnAffordable = ISButton:new(cw - PAD - 92, Y_SEARCH, 92, 24, "Can afford", self, PhoneShopUI.toggleAffordable)
    self.btnAffordable:initialise()
    self:addChild(self.btnAffordable)

    self.itemList = PhoneShopList:new(PAD, Y_LIST, cw - PAD * 2, ch - Y_LIST - Y_BTM - 10)
    self.itemList:initialise()
    self.itemList.onSelect = function(entry)
        self:setStatus(entry.label .. "  —  $" .. entry.price, C.white.r, C.white.g, C.white.b)
    end
    self:addChild(self.itemList)

    self.btnAction = ISButton:new(PAD, ch - PAD - ROW_H, cw - PAD * 2, ROW_H, "BUY ITEM", self, PhoneShopUI.doAction)
    self.btnAction:initialise()
    self:addChild(self.btnAction)
    self:refreshModeStyle()
    self:updateCatStyle()
    self:updateAffordableStyle()
    self:applyFilter()
end

function PhoneShopUI:render()
    ISCollapsableWindow.render(self)
    self:drawRect(0, 0, self.width, self.height, 0.35, col(C.bg))

    local balLabel = (PhoneShop.economyRules and PhoneShop.economyRules()) and "Buying power:" or "Balance:"
    local balW = getTextManager():MeasureStringX(UIFont.Small, balLabel)
    self:drawText(balLabel, PAD, Y_BAL, col(C.muted))
    self:drawText("$" .. PhoneShopClient.Balance, PAD + balW + 6, Y_BAL, col(C.orange))

    self:drawText("Search items...", PAD, Y_SEARCH - 14, col(C.muted))
    if self.listHint and self.listHint ~= "" then
        self:drawText(self.listHint, PAD, Y_DIV - 14, col(C.muted))
    end
    self:drawRect(PAD, Y_DIV, self.width - PAD * 2, 1, 1, col(C.divider))
    self:drawText("Item", PAD + COL_NAME, Y_COLHDR, col(C.muted))
    self:drawText("Price", PAD + COL_PRICE, Y_COLHDR, col(C.muted))
    self:drawText(self.statusText, PAD + 4, self.height - PAD - ROW_H - 22,
        self.statusR, self.statusG, self.statusB, 1, UIFont.Small)
end

function PhoneShopUI:setStatus(text, r, g, b)
    self.statusText = text or ""
    self.statusR, self.statusG, self.statusB = r or C.muted.r, g or C.muted.g, b or C.muted.b
end

function PhoneShopUI:applyFilter()
    if PhoneShop.isSinglePlayer() then
        refreshBalance()
    end
    local src = self.mode == "buy" and PhoneShopConfig.BuyList or PhoneShopConfig.SellList
    local base, stats = filterList(self.mode, src, self.activeCat)
    local query = self.searchText or ""
    local balance = PhoneShopClient.Balance
    local affordableOnly = self.mode == "buy" and self.showAffordableOnly
    local out = {}
    for _, e in ipairs(base) do
        if matchesSearch(e, query) then
            if not affordableOnly or e.price <= balance then
                table.insert(out, e)
            end
        end
    end
    if stats and stats.total > stats.visible then
        local hidden = stats.total - stats.visible
        self.listHint = string.format(
            "Showing %d of %d (%d hidden — mods not loaded)",
            stats.visible, stats.total, hidden
        )
        if stats.hiddenByPrefix then
            local rows = {}
            for prefix, count in pairs(stats.hiddenByPrefix) do
                table.insert(rows, { prefix = prefix, count = count })
            end
            table.sort(rows, function(a, b) return a.count > b.count end)
            local parts = {}
            for i = 1, math.min(4, #rows) do
                table.insert(parts, rows[i].prefix .. "(" .. rows[i].count .. ")")
            end
            if #parts > 0 then
                self.listHint = self.listHint .. " — " .. table.concat(parts, ", ")
            end
        end
    elseif stats then
        local rev = PhoneShop.listRevision or 0
        local listCount = self.mode == "buy" and #(PhoneShopConfig.BuyList or {}) or #(PhoneShopConfig.SellList or {})
        self.listHint = string.format("%d items in this category (list rev %d, %d loaded)", stats.visible, rev, listCount)
    else
        self.listHint = ""
    end
    if query ~= "" or affordableOnly then
        self.listHint = self.listHint .. string.format(" · %d match filters", #out)
    end
    if PhoneShopClient.listMismatch then
        local prefix = "MP WARNING: your shop files differ from the server — update your mod files or trades may fail."
        if self.listHint and self.listHint ~= "" then
            self.listHint = prefix .. " | " .. self.listHint
        else
            self.listHint = prefix
        end
    end
    local emptyText = "No items found."
    if affordableOnly and query ~= "" then
        emptyText = "No affordable matches for your search."
    elseif affordableOnly then
        emptyText = "Nothing you can afford in this category."
    elseif query ~= "" then
        emptyText = "No matches for your search."
    elseif self.activeCat ~= "All" then
        emptyText = "No items in this category."
    end
    self.itemList.checkAfford = self.mode == "buy"
    self.itemList:setEntries(out, emptyText)
end

function PhoneShopUI:refreshModeStyle()
    local buy = self.mode == "buy"
    applyBtnStyle(self.btnBuy, buy and C.orange or C.chipOff)
    applyBtnStyle(self.btnSell, buy and C.chipOff or C.orange)
    self.btnAction:setTitle(buy and "BUY ITEM" or "SELL ITEM")
    applyBtnStyle(self.btnAction, C.orange)
    if self.btnAffordable then
        self.btnAffordable:setVisible(buy)
    end
    if not buy then
        self.showAffordableOnly = false
        self:updateAffordableStyle()
    end
end

function PhoneShopUI:updateCatStyle()
    for _, btn in ipairs(self.catBtns) do
        applyBtnStyle(btn, btn.catName == self.activeCat and C.orange or C.chipOff)
    end
end

function PhoneShopUI:updateAffordableStyle()
    if not self.btnAffordable then return end
    applyBtnStyle(self.btnAffordable, self.showAffordableOnly and C.orange or C.chipOff)
end

function PhoneShopUI:toggleAffordable()
    if self.mode ~= "buy" then return end
    self.showAffordableOnly = not self.showAffordableOnly
    self:updateAffordableStyle()
    self:applyFilter()
end

function PhoneShopUI:onCatClick(btn)
    self.activeCat = btn.catName
    self:updateCatStyle()
    self:applyFilter()
end

function PhoneShopUI:switchBuy()
    self.mode = "buy"
    self:refreshModeStyle()
    self:applyFilter()
end

function PhoneShopUI:switchSell()
    self.mode = "sell"
    self:refreshModeStyle()
    self:applyFilter()
end

function PhoneShopUI:doAction()
    local entry = self.itemList:getSelected()
    if not entry then
        self:setStatus("Select an item first.", C.orange.r, C.orange.g, C.orange.b)
        return
    end
    local player = PhoneShopClient.getPlayer()
    if not player then return end
    if self.mode == "buy" then
        if PhoneShop.isSinglePlayer() then
            if PhoneShopClient.Balance < entry.price then
                self:setStatus("Not enough money.", C.danger.r, C.danger.g, C.danger.b)
                return
            end
        elseif PhoneShopClient.balanceSynced and PhoneShopClient.Balance < entry.price then
            self:setStatus("Not enough money.", C.danger.r, C.danger.g, C.danger.b)
            return
        end
        doTrade(PhoneShop.CMD.BUY, entry.itemType)
    else
        if not PhoneShop.hasItem(player, entry.itemType) then
            self:setStatus("You don't have that item.", C.danger.r, C.danger.g, C.danger.b)
            return
        end
        doTrade(PhoneShop.CMD.SELL, entry.itemType)
    end
end

function PhoneShopUI:onClickClose()
    self:close()
end

function PhoneShopUI:close()
    self:setVisible(false)
    self:removeFromUIManager()
    PhoneShopClient.Window = nil
    local player = PhoneShopClient.getPlayer()
    if player then ISTimedActionQueue.add(ISPhoneShopCloseAction:new(player)) end
end

function PhoneShopClient.OpenShopUI(player)
    PhoneShopClient.activePlayer = PhoneShop.resolvePlayer(player)
    if PhoneShop.reloadShopLists then
        PhoneShop.reloadShopLists()
    end
    PhoneShopClient.resetItemCaches()
    PhoneShopClient.listMismatch = false
    PhoneShopClient.balanceSynced = false
    if type(isMultiplayer) == "function" and isMultiplayer() then
        sendClientCommand(PhoneShop.MODULE, PhoneShop.CMD.GET_LIST_INFO, {})
    else
        refreshBalance()
        PhoneShopClient.balanceSynced = true
    end
    if PhoneShopClient.Window then
        PhoneShopClient.Window:setVisible(true)
        PhoneShopClient.Window:bringToTop()
        PhoneShopClient.Window:applyFilter()
        return
    end
    local sw, sh = getCore():getScreenWidth(), getCore():getScreenHeight()
    local win = PhoneShopUI:new(math.floor((sw - WIN_W) / 2), math.max(60, math.floor((sh - WIN_H) / 2)), WIN_W, WIN_H)
    win:initialise()
    win:addToUIManager()
    PhoneShopClient.Window = win
end

local function onServerCommand(module, command, args)
    if module ~= PhoneShop.MODULE then return end
    if command == PhoneShop.CMD.RESULT then
        showResult(args)
    elseif command == PhoneShop.CMD.LIST_INFO then
        PhoneShopClient.onServerListInfo(args)
    end
end

local function resolveContextPhone(items)
    if not items then return nil end
    if ISInventoryPane and ISInventoryPane.getActualItems then
        local actual = ISInventoryPane.getActualItems(items)
        if actual then
            for i = 1, #actual do
                local entry = actual[i]
                if entry and entry.getType and entry:getType() == PhoneShopConfig.PhoneItem then
                    return entry
                end
            end
        end
    end
    for _, v in ipairs(items) do
        local entry = (type(v) == "table" and v.items) and v.items[1] or v
        if entry and entry.getType and entry:getType() == PhoneShopConfig.PhoneItem then
            return entry
        end
    end
    return nil
end

local function onContextMenu(playerNum, context, items)
    local who = PhoneShop.resolvePlayer(playerNum)
    if not who or not context then return end
    local phoneItem = resolveContextPhone(items)
    if not phoneItem then return end
    context:addOption("IKappaID Phone Shop", phoneItem, function(item)
        local player = PhoneShop.resolvePlayer(who)
        if not player then return end
        ISTimedActionQueue.add(ISPhoneShopOpenAction:new(player, item or phoneItem))
    end)
end

Events.OnFillInventoryObjectContextMenu.Add(onContextMenu)
Events.OnServerCommand.Add(onServerCommand)
