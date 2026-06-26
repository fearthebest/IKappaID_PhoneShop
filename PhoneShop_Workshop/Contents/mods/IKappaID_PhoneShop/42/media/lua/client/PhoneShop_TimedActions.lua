-- PhoneShop — timed actions

require "TimedActions/ISBaseTimedAction"
require "PhoneShop_Config"

ISPhoneShopOpenAction = ISBaseTimedAction:derive("ISPhoneShopOpenAction")

function ISPhoneShopOpenAction:new(character, phoneItem)
    local o = ISBaseTimedAction.new(self, character)
    o.character = character
    o.phoneItem = phoneItem
    o.maxTime = PhoneShopConfig.OpenDuration
    o.stopOnWalk = true
    o.stopOnRun = true
    o.useProgressBar = true
    return o
end

function ISPhoneShopOpenAction:isValid()
    local ch = self.character
    if not ch or not ch.getInventory or not self.phoneItem then
        return false
    end
    return ch:getInventory():contains(self.phoneItem)
end

function ISPhoneShopOpenAction:waitToStart() return false end

function ISPhoneShopOpenAction:start()
    if self.character and self.character.Say then
        self.character:Say(PhoneShopConfig.HaloOpen)
    end
end

function ISPhoneShopOpenAction:getJobName() return "Connecting..." end
function ISPhoneShopOpenAction:update() end

function ISPhoneShopOpenAction:perform()
    ISBaseTimedAction.perform(self)
    PhoneShopClient.OpenShopUI(self.character)
end

function ISPhoneShopOpenAction:stop()
    ISBaseTimedAction.stop(self)
end

ISPhoneShopCloseAction = ISBaseTimedAction:derive("ISPhoneShopCloseAction")

function ISPhoneShopCloseAction:new(character)
    local o = ISBaseTimedAction.new(self, character)
    o.character = character
    o.maxTime = PhoneShopConfig.CloseDuration
    o.stopOnWalk = false
    o.stopOnRun = true
    o.useProgressBar = true
    return o
end

function ISPhoneShopCloseAction:isValid()
    return self.character ~= nil and self.character.getInventory ~= nil
end
function ISPhoneShopCloseAction:waitToStart() return false end

function ISPhoneShopCloseAction:start()
    if self.character and self.character.Say then
        self.character:Say(PhoneShopConfig.HaloClose)
    end
end

function ISPhoneShopCloseAction:getJobName() return "Hanging up..." end
function ISPhoneShopCloseAction:update() end

function ISPhoneShopCloseAction:perform()
    ISBaseTimedAction.perform(self)
end

function ISPhoneShopCloseAction:stop()
    ISBaseTimedAction.stop(self)
end
