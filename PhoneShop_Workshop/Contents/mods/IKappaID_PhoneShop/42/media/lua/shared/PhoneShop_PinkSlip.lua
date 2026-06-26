-- PhoneShop — prefilled pink slip minting (server / SP local sim)

require "PhoneShop_Shared"

PhoneShopPinkSlip = PhoneShopPinkSlip or {}

local TAG = PhoneShop.PINKSLIP_TAG or "@ps:"

function PhoneShop.isPinkSlipItemType(itemType)
    return type(itemType) == "string" and itemType:sub(1, #TAG) == TAG
end

function PhoneShop.pinkSlipVehicleScript(itemType)
    if not PhoneShop.isPinkSlipItemType(itemType) then return nil end
    local scriptName = itemType:sub(#TAG + 1)
    if scriptName == "" then return nil end
    return scriptName
end

function PhoneShop.pinkSlipShopKey(vehicleScript)
    if not vehicleScript or vehicleScript == "" then return nil end
    return TAG .. vehicleScript
end

function PhoneShop.vehicleScriptExists(scriptName)
    if not scriptName or scriptName == "" then return false end
    local sm = getScriptManager and getScriptManager() or nil
    if not sm then return false end
    if sm.getVehicleScript then
        local vs = sm:getVehicleScript(scriptName)
        if vs then return true end
    end
    if sm.getAllVehicleScripts then
        local scripts = sm:getAllVehicleScripts()
        if scripts and scripts.size and scripts.get then
            for i = 0, scripts:size() - 1 do
                local sc = scripts:get(i)
                if sc and sc.getFullName and sc:getFullName() == scriptName then
                    return true
                end
                if sc and sc.getName and sc:getName() == scriptName then
                    return true
                end
            end
        end
    end
    return false
end

function PhoneShop.isShopItemAvailable(itemType, entry)
    if not ScriptManager or not ScriptManager.instance or not ScriptManager.instance.FindItem then
        return true
    end
    if PhoneShop.isPinkSlipItemType(itemType) then
        local slipType = "IKappaIDPinkSlip.PinkSlip"
        if ScriptManager.instance:FindItem(slipType) == nil then
            return false, "Pink Slip mod not loaded on server."
        end
        local scriptName = entry and entry.vehicleScript or PhoneShop.pinkSlipVehicleScript(itemType)
        if not scriptName or not PhoneShop.vehicleScriptExists(scriptName) then
            return false, "Vehicle mod not loaded on server."
        end
        return true
    end
    if ScriptManager.instance:FindItem(itemType) == nil then
        return false, "Item mod not loaded on server."
    end
    return true
end

local function pinkSlipCore()
    if IKappaPinkSlip and IKappaPinkSlip.writeSlipPayload then
        return IKappaPinkSlip
    end
    if getActivatedMods then
        local mods = getActivatedMods()
        if mods and mods.size then
            for i = 0, mods:size() - 1 do
                if mods:get(i) == "IKappaIDPinkSlip" then
                    if require then
                        require "IKappaIDPinkSlip_Shared"
                    end
                    break
                end
            end
        end
    end
    if IKappaPinkSlip and IKappaPinkSlip.writeSlipPayload then
        return IKappaPinkSlip
    end
    return nil
end

local function countFilledSlips(player, core)
    if not player or not core or not core.isFilledSlipItem then return 0 end
    local inv = player.getInventory and player:getInventory() or nil
    if not inv or not inv.getAllEvalRecurse then return 0 end
    local items = inv:getAllEvalRecurse(function(item)
        return item and core.isFilledSlipItem(item)
    end)
    if items and items.size then return items:size() end
    return 0
end

function PhoneShopPinkSlip.mint(player, entry)
    local core = pinkSlipCore()
    if not core then
        return false, "Pink Slip mod not loaded"
    end
    if not player then
        return false, "No player"
    end
    if not core.isEnabled or not core.isEnabled() then
        return false, "Pink Slip system is disabled"
    end

    local scriptName = entry.vehicleScript or PhoneShop.pinkSlipVehicleScript(entry.itemType)
    if not scriptName or scriptName == "" then
        return false, "Invalid vehicle"
    end
    if not PhoneShop.vehicleScriptExists(scriptName) then
        return false, "Vehicle not available (mod not loaded)"
    end

    local maxSlips = core.getMaxFilledSlips and core.getMaxFilledSlips() or 5
    if countFilledSlips(player, core) >= maxSlips then
        return false, "Pink Slip cap reached (" .. tostring(maxSlips) .. ")"
    end

    local inv = player.getInventory and player:getInventory() or nil
    if not inv then
        return false, "No inventory"
    end

    local slipType = core.FILLED_SLIP_TYPE or "IKappaIDPinkSlip.PinkSlip"
    local slip = nil
    local slipInInv = false
    if instanceItem then
        slip = instanceItem(slipType)
    end
    if not slip and inv.AddItem then
        slip = inv:AddItem(slipType)
        slipInInv = slip ~= nil
    end
    if not slip then
        return false, "Could not create Pink Slip"
    end

    local snap = {
        schemaVersion = core.SCHEMA_VERSION or 1,
        capturedAt = (os and os.time and os.time()) or 0,
        scriptName = scriptName,
        skinIndex = -1,
        hasKey = entry.hasKey and true or false,
        parts = {},
        modData = {},
    }

    local ownerName = (player.getUsername and player:getUsername()) or ""
    snap.modData = snap.modData or {}
    if core.OWNER_LOCK_KEY then
        snap.modData[core.OWNER_LOCK_KEY] = ownerName
    end

    local uid = (core.mintSlipUid and core.mintSlipUid(player)) or ("shop_" .. tostring((os and os.time and os.time()) or 0))
    if core.ensureSnapshotVehicleUid then
        core.ensureSnapshotVehicleUid(snap, uid)
    end
    if not core.writeSlipPayload(slip, snap, uid, ownerName) then
        if slipInInv and inv.Remove then inv:Remove(slip) end
        return false, "Could not write Pink Slip data"
    end

    if not slipInInv and inv.AddItem then
        inv:AddItem(slip)
    end
    if sendAddItemToContainer then
        sendAddItemToContainer(inv, slip)
    end
    if inv.setDrawDirty then
        inv:setDrawDirty(true)
    end

    return true, slip
end
