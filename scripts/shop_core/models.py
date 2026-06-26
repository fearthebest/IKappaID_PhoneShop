from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ShopEntry:
    item_type: str
    label: str
    price: int
    category: str

    def line(self) -> str:
        return f"{self.item_type}|{self.label}|{self.price}|{self.category}"


@dataclass
class ScannedItem:
    item_type: str
    label: str
    price: int
    category: str
    source: str
    included: bool = True

    def to_entry(self) -> ShopEntry:
        return ShopEntry(self.item_type, self.label, self.price, self.category)
