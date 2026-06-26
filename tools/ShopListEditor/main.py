#!/usr/bin/env python3
"""IKappaID Phone Shop — List Editor (dark UI)."""

from __future__ import annotations

import json
import re
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

EDITOR_DIR = Path(__file__).resolve().parent
# Bundled inside Zomboid/Workshop/IKappaID_PhoneShop/ListEditor — parent is the upload folder.
# In dev repo: tools/ShopListEditor with shop_core copied locally OR scripts/shop_core on path.
if (EDITOR_DIR / "shop_core").is_dir():
    BUNDLE_ROOT = EDITOR_DIR.parent
    sys.path.insert(0, str(EDITOR_DIR))
else:
    BUNDLE_ROOT = EDITOR_DIR.parents[2]
    sys.path.insert(0, str(BUNDLE_ROOT / "scripts"))
sys.path.insert(0, str(EDITOR_DIR))

from shop_core import (  # noqa: E402
    SHOP_CATEGORIES,
    ScannedItem,
    default_phoneshop_path,
    discover_phoneshop_locations,
    format_preview_text,
    format_vanilla_status,
    has_vanilla_baseline,
    parse_shop_list,
    preview_merge,
    restore_from_backup,
    restore_vanilla_baseline,
    save_vanilla_baseline,
    scan_mod_folder,
    sync_phoneshop_lists,
    write_shop_list,
)
from theme import (  # noqa: E402
    BG,
    BORDER,
    CARD,
    CHIP,
    MUTED,
    ORANGE,
    ORANGE_DIM,
    ORANGE_HOVER,
    SELECT,
    TEXT,
)

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
JUNK_RE = re.compile(
    r"(?i)([/\\]fx[/\\]|[/\\]spawners[/\\]|_Weapon$|_Explosion$|FakeItem|Bullet_\d+)",
)


def load_config() -> dict:
    if CONFIG_PATH.is_file():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def save_config(data: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def row_is_junk(row: ScannedItem) -> bool:
    blob = f"{row.item_type} {row.source}"
    return bool(JUNK_RE.search(blob))


def setup_dark_treeview(root: tk.Misc) -> ttk.Style:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(
        "Shop.Treeview",
        background=CARD,
        foreground=TEXT,
        fieldbackground=CARD,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        rowheight=28,
        font=("Segoe UI", 10),
    )
    style.configure(
        "Shop.Treeview.Heading",
        background=CHIP,
        foreground=ORANGE,
        relief="flat",
        font=("Segoe UI", 10, "bold"),
    )
    style.map(
        "Shop.Treeview",
        background=[("selected", SELECT)],
        foreground=[("selected", TEXT)],
    )
    return style


class ShopListEditorApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("IKappaID Phone Shop — List Editor")
        self.geometry("1140x720")
        self.minsize(920, 580)
        self.configure(fg_color=BG)

        cfg = load_config()
        self.mod_var = tk.StringVar(value=cfg.get("mod_folder", ""))
        shop_path, shop_reason = default_phoneshop_path(BUNDLE_ROOT, CONFIG_PATH)
        self.shop_var = tk.StringVar(value=str(shop_path) if shop_path else "")
        self.module_var = tk.StringVar(value=cfg.get("module_prefix", ""))
        self.sell_pct_var = tk.StringVar(value=str(cfg.get("sell_percent", 20)))
        self.filter_var = tk.StringVar()
        self.hide_junk_var = tk.BooleanVar(value=cfg.get("hide_junk", True))
        self.sync_var = tk.BooleanVar(value=cfg.get("sync_after_write", True))
        self.status_var = tk.StringVar(value=shop_reason)

        self.scanned: list[ScannedItem] = []
        self.detected_module = ""
        self._tree_style = setup_dark_treeview(self)
        self._build_ui()
        self.filter_var.trace_add("write", lambda *_: self.refresh_tree())
        self.hide_junk_var.trace_add("write", lambda *_: self.refresh_tree())

    def _btn(self, parent, text: str, command, *, secondary: bool = False, width: int = 0, height: int = 0) -> ctk.CTkButton:
        kw: dict = {"text": text, "command": command, "corner_radius": 6}
        if secondary:
            kw["fg_color"] = CHIP
            kw["hover_color"] = BORDER
            kw["border_color"] = BORDER
        else:
            kw["fg_color"] = ORANGE
            kw["hover_color"] = ORANGE_HOVER
            kw["border_color"] = ORANGE_DIM
        if width:
            kw["width"] = width
        if height:
            kw["height"] = height
        return ctk.CTkButton(parent, **kw)

    def _build_ui(self) -> None:
        header = ctk.CTkFrame(self, fg_color=CARD, corner_radius=8)
        header.pack(fill=tk.X, padx=12, pady=(12, 6))

        ctk.CTkLabel(header, text="Source mod folder", text_color=MUTED).grid(row=0, column=0, sticky=tk.W, padx=10, pady=(8, 2))
        ctk.CTkEntry(header, textvariable=self.mod_var).grid(row=1, column=0, sticky=tk.EW, padx=10, pady=(0, 8))
        self._btn(header, "Browse…", self.browse_mod, secondary=True, width=90).grid(row=1, column=1, padx=(0, 10), pady=(0, 8))

        ctk.CTkLabel(header, text="Phone Shop lists folder", text_color=MUTED).grid(row=0, column=2, sticky=tk.W, padx=10, pady=(8, 2))
        ctk.CTkEntry(header, textvariable=self.shop_var).grid(row=1, column=2, sticky=tk.EW, padx=10, pady=(0, 8))
        shop_btns = ctk.CTkFrame(header, fg_color="transparent")
        shop_btns.grid(row=1, column=3, padx=(0, 10), pady=(0, 8))
        self._btn(shop_btns, "Detect", self.detect_phoneshop, secondary=True, width=72).pack(side=tk.LEFT, padx=(0, 4))
        self._btn(shop_btns, "Browse…", self.browse_shop, secondary=True, width=72).pack(side=tk.LEFT)

        ctk.CTkLabel(header, text="Module prefix (optional)", text_color=MUTED).grid(row=2, column=0, sticky=tk.W, padx=10, pady=(0, 2))
        ctk.CTkEntry(header, textvariable=self.module_var, width=160).grid(row=3, column=0, sticky=tk.W, padx=10, pady=(0, 10))
        ctk.CTkLabel(header, text="Auto from mod.info if empty", text_color=MUTED).grid(row=3, column=0, sticky=tk.W, padx=(180, 10))

        header.columnconfigure(0, weight=1)
        header.columnconfigure(2, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill=tk.X, padx=12, pady=4)

        left = ctk.CTkFrame(toolbar, fg_color="transparent")
        left.pack(side=tk.LEFT)
        self._btn(left, "Scan mod", self.scan).pack(side=tk.LEFT, padx=(0, 4))
        self._btn(left, "Include all", lambda: self.set_all_included(True), secondary=True).pack(side=tk.LEFT, padx=2)
        self._btn(left, "Exclude all", lambda: self.set_all_included(False), secondary=True).pack(side=tk.LEFT, padx=2)
        self._btn(left, "Toggle selected", self.toggle_selected, secondary=True).pack(side=tk.LEFT, padx=2)

        ctk.CTkLabel(left, text="Sell %", text_color=MUTED).pack(side=tk.LEFT, padx=(12, 4))
        ctk.CTkEntry(left, textvariable=self.sell_pct_var, width=48).pack(side=tk.LEFT)
        self._btn(left, "Price…", self.apply_price, secondary=True).pack(side=tk.LEFT, padx=(8, 2))
        self._btn(left, "Category…", self.apply_category, secondary=True).pack(side=tk.LEFT, padx=2)

        filter_row = ctk.CTkFrame(self, fg_color="transparent")
        filter_row.pack(fill=tk.X, padx=12, pady=2)
        ctk.CTkLabel(filter_row, text="Search", text_color=MUTED).pack(side=tk.LEFT)
        ctk.CTkEntry(filter_row, textvariable=self.filter_var, width=280, placeholder_text="item id, label, category…").pack(
            side=tk.LEFT, padx=8
        )
        ctk.CTkCheckBox(
            filter_row,
            text="Hide junk (spawners, *_Weapon, fx)",
            variable=self.hide_junk_var,
            fg_color=ORANGE,
            hover_color=ORANGE_HOVER,
        ).pack(side=tk.LEFT, padx=8)
        ctk.CTkCheckBox(
            filter_row,
            text="Sync all Phone Shop folders after write",
            variable=self.sync_var,
            fg_color=ORANGE,
            hover_color=ORANGE_HOVER,
        ).pack(side=tk.LEFT, padx=8)

        table_wrap = ctk.CTkFrame(self, fg_color=CARD, corner_radius=8)
        table_wrap.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        cols = ("inc", "item_type", "label", "price", "category", "source")
        self.tree = ttk.Treeview(table_wrap, columns=cols, show="headings", selectmode="extended", style="Shop.Treeview")
        headings = {
            "inc": "✓",
            "item_type": "Item ID",
            "label": "Label",
            "price": "Price",
            "category": "Category",
            "source": "Source file",
        }
        widths = {"inc": 36, "item_type": 210, "label": 190, "price": 72, "category": 118, "source": 300}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor=tk.W)
        self.tree.bind("<Double-1>", self.on_double_click)
        yscroll = ctk.CTkScrollbar(table_wrap, command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=8)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 8), pady=8)

        vanilla_row = ctk.CTkFrame(self, fg_color=CARD, corner_radius=8)
        vanilla_row.pack(fill=tk.X, padx=12, pady=(0, 6))
        self.vanilla_status_var = tk.StringVar(value="")
        ctk.CTkLabel(vanilla_row, text="Safety backup", text_color=ORANGE, font=ctk.CTkFont(weight="bold")).pack(
            side=tk.LEFT, padx=(12, 8), pady=10
        )
        ctk.CTkLabel(vanilla_row, textvariable=self.vanilla_status_var, text_color=MUTED).pack(side=tk.LEFT, padx=4)
        self._btn(vanilla_row, "Save vanilla baseline", self.save_vanilla, secondary=True).pack(side=tk.RIGHT, padx=8, pady=8)
        self._btn(vanilla_row, "Restore vanilla", self.restore_vanilla, secondary=True).pack(side=tk.RIGHT, padx=0, pady=8)
        self._btn(vanilla_row, "Undo last write", self.undo_write, secondary=True).pack(side=tk.RIGHT, padx=0, pady=8)

        action_bar = ctk.CTkFrame(self, fg_color=CARD, corner_radius=8)
        action_bar.pack(fill=tk.X, padx=12, pady=(0, 6))
        ctk.CTkLabel(
            action_bar,
            text="Merge scanned items into buy_list.txt + sell_list.txt",
            text_color=MUTED,
        ).pack(side=tk.LEFT, padx=12, pady=14)
        self._btn(
            action_bar,
            "WRITE BUY + SELL LISTS",
            self.write_lists,
            width=220,
            height=40,
        ).pack(side=tk.RIGHT, padx=12, pady=10)

        footer = ctk.CTkFrame(self, fg_color=CARD, corner_radius=8)
        footer.pack(fill=tk.X, padx=12, pady=(0, 12))
        ctk.CTkLabel(footer, textvariable=self.status_var, text_color=MUTED, anchor=tk.W).pack(
            fill=tk.X, padx=12, pady=10
        )
        self.after(200, self.refresh_vanilla_status)

    def refresh_vanilla_status(self) -> None:
        shop = self.shop_var.get().strip()
        if shop and Path(shop).is_dir():
            self.vanilla_status_var.set(format_vanilla_status(Path(shop)))
        else:
            self.vanilla_status_var.set("Set Phone Shop folder first")

    def browse_mod(self) -> None:
        path = filedialog.askdirectory(title="Select mod folder")
        if path:
            self.mod_var.set(path)

    def browse_shop(self) -> None:
        path = filedialog.askdirectory(title="Select phoneshop folder")
        if path:
            self.shop_var.set(path)
            self.refresh_vanilla_status()

    def detect_phoneshop(self) -> None:
        preferred = self.shop_var.get().strip() or None
        locations = discover_phoneshop_locations(BUNDLE_ROOT, preferred=preferred)
        if not locations:
            messagebox.showwarning(
                "Detect Phone Shop",
                "No phoneshop folder found.\n\n"
                "Looked in Zomboid Workshop, dev repo, Steam cache, and Zomboid mods.\n"
                "Use Browse to set the folder manually.",
            )
            return
        if len(locations) == 1:
            loc = locations[0]
            self.shop_var.set(str(loc.path))
            self.status_var.set(f"Detected: {loc.source}")
            self.refresh_vanilla_status()
            self._persist_config()
            return
        self._pick_location_dialog(locations)

    def _pick_location_dialog(self, locations) -> None:
        win = ctk.CTkToplevel(self)
        win.title("Choose Phone Shop folder")
        win.geometry("640x420")
        win.transient(self)
        win.grab_set()
        ctk.CTkLabel(
            win,
            text="Multiple Phone Shop folders found:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor=tk.W, padx=16, pady=(16, 8))
        box = ctk.CTkTextbox(win, height=280)
        box.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
        lines = []
        for i, loc in enumerate(locations[:12], 1):
            hint = ""
            if loc.buy_mtime:
                hint = datetime.fromtimestamp(loc.buy_mtime).strftime(" — %Y-%m-%d %H:%M")
            lines.append(f"{i}. [{loc.source}]{hint}\n   {loc.path}\n")
        box.insert("1.0", "".join(lines))
        box.configure(state="disabled")
        var = tk.StringVar(value="1")

        def apply() -> None:
            try:
                idx = int(var.get().strip()) - 1
            except ValueError:
                idx = 0
            idx = max(0, min(idx, len(locations) - 1))
            loc = locations[idx]
            self.shop_var.set(str(loc.path))
            self.status_var.set(f"Using: {loc.source}")
            self.refresh_vanilla_status()
            win.destroy()
            self._persist_config()

        pick = ctk.CTkFrame(win, fg_color="transparent")
        pick.pack(fill=tk.X, padx=16, pady=8)
        ctk.CTkLabel(pick, text="Use #").pack(side=tk.LEFT)
        ctk.CTkEntry(pick, textvariable=var, width=48).pack(side=tk.LEFT, padx=8)
        self._btn(pick, "Apply", apply).pack(side=tk.LEFT)

    def scan(self) -> None:
        mod_path = Path(self.mod_var.get().strip())
        if not mod_path.is_dir():
            messagebox.showerror("Scan", "Source mod folder does not exist.")
            return
        try:
            prefix = self.module_var.get().strip() or None
            self.scanned, self.detected_module, scripts = scan_mod_folder(mod_path, module_prefix=prefix)
        except FileNotFoundError as exc:
            messagebox.showerror("Scan", str(exc))
            return
        if not self.module_var.get().strip():
            self.module_var.set(self.detected_module)
        self.refresh_tree()
        shown = len(self._filtered_rows())
        junk = sum(1 for r in self.scanned if row_is_junk(r))
        self.status_var.set(
            f"Scanned {len(self.scanned)} items ({shown} shown) — {self.detected_module} — {junk} junk hidden"
        )
        self._persist_config()

    def _persist_config(self) -> None:
        try:
            sell_pct = int(float(self.sell_pct_var.get() or 20))
        except ValueError:
            sell_pct = 20
        save_config(
            {
                "mod_folder": self.mod_var.get().strip(),
                "phoneshop_folder": self.shop_var.get().strip(),
                "module_prefix": self.module_var.get().strip(),
                "sell_percent": sell_pct,
                "hide_junk": self.hide_junk_var.get(),
                "sync_after_write": self.sync_var.get(),
            }
        )

    def _filtered_rows(self) -> list[ScannedItem]:
        q = self.filter_var.get().strip().lower()
        hide_junk = self.hide_junk_var.get()
        out: list[ScannedItem] = []
        for row in self.scanned:
            if hide_junk and row_is_junk(row):
                continue
            if q:
                blob = f"{row.item_type} {row.label} {row.category} {row.source}".lower()
                if q not in blob:
                    continue
            out.append(row)
        return out

    def refresh_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(self._filtered_rows()):
            self.tree.insert(
                "",
                tk.END,
                iid=str(i),
                values=(
                    "✓" if row.included else " ",
                    row.item_type,
                    row.label,
                    row.price,
                    row.category,
                    row.source,
                ),
            )

    def _row_index(self, iid: str) -> int:
        row = self._filtered_rows()[int(iid)]
        return self.scanned.index(row)

    def on_double_click(self, event) -> None:
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.tree.identify_column(event.x)
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        idx = self._row_index(iid)
        row = self.scanned[idx]
        if col == "#1":
            row.included = not row.included
            self.refresh_tree()
            return
        if col == "#4":
            dialog = ctk.CTkInputDialog(text=f"Price for {row.item_type}:", title="Price")
            raw = dialog.get_input()
            if raw and raw.isdigit():
                row.price = int(raw)
                self.refresh_tree()
            return
        if col == "#5":
            self._pick_category([idx])

    def set_all_included(self, value: bool) -> None:
        for row in self._filtered_rows():
            row.included = value
        self.refresh_tree()

    def toggle_selected(self) -> None:
        for iid in self.tree.selection():
            idx = self._row_index(iid)
            self.scanned[idx].included = not self.scanned[idx].included
        self.refresh_tree()

    def _selected_indices(self) -> list[int]:
        return [self._row_index(iid) for iid in self.tree.selection()]

    def apply_price(self) -> None:
        indices = self._selected_indices()
        if not indices:
            messagebox.showinfo("Price", "Select one or more rows first.")
            return
        dialog = ctk.CTkInputDialog(text="Set price for selected items:", title="Bulk price")
        raw = dialog.get_input()
        if not raw or not raw.isdigit():
            return
        price = int(raw)
        for i in indices:
            self.scanned[i].price = price
        self.refresh_tree()

    def apply_category(self) -> None:
        indices = self._selected_indices()
        if not indices:
            messagebox.showinfo("Category", "Select one or more rows first.")
            return
        self._pick_category(indices)

    def _pick_category(self, indices: list[int]) -> None:
        win = ctk.CTkToplevel(self)
        win.title("Category")
        win.geometry("320x160")
        win.transient(self)
        win.grab_set()
        var = tk.StringVar(value=self.scanned[indices[0]].category)
        ctk.CTkLabel(win, text="Category").pack(padx=16, pady=(16, 8))
        menu = ctk.CTkOptionMenu(win, variable=var, values=SHOP_CATEGORIES, fg_color=CHIP)
        menu.pack(padx=16, pady=4)

        def ok() -> None:
            cat = var.get()
            for i in indices:
                self.scanned[i].category = cat
            win.destroy()
            self.refresh_tree()

        self._btn(win, "OK", ok).pack(pady=12)

    def _ask_preview(self, text: str) -> bool:
        win = ctk.CTkToplevel(self)
        win.title("Confirm write")
        win.geometry("560x480")
        win.transient(self)
        win.grab_set()
        ctk.CTkLabel(win, text="Preview changes", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor=tk.W, padx=16, pady=(16, 8)
        )
        box = ctk.CTkTextbox(win, font=ctk.CTkFont(family="Consolas", size=12))
        box.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
        box.insert("1.0", text)
        box.configure(state="disabled")
        result = {"ok": False}

        def yes() -> None:
            result["ok"] = True
            win.destroy()

        def no() -> None:
            win.destroy()

        btns = ctk.CTkFrame(win, fg_color="transparent")
        btns.pack(pady=12)
        self._btn(btns, "Write", yes).pack(side=tk.LEFT, padx=8)
        self._btn(btns, "Cancel", no, secondary=True).pack(side=tk.LEFT, padx=8)
        win.wait_window()
        return result["ok"]

    def write_lists(self) -> None:
        if not self.scanned:
            messagebox.showerror("Write", "Scan a mod first.")
            return
        shop = Path(self.shop_var.get().strip())
        if not shop.is_dir():
            messagebox.showerror("Write", "Phone Shop lists folder does not exist.")
            return
        included = [r for r in self.scanned if r.included]
        if not included:
            messagebox.showerror("Write", "No items included.")
            return
        if not has_vanilla_baseline(shop):
            if messagebox.askyesno(
                "Save vanilla baseline first?",
                "No vanilla baseline is saved for this Phone Shop folder.\n\n"
                "Save the current lists as your safe restore point before merging?",
            ):
                try:
                    save_vanilla_baseline(shop, note="auto before first write")
                    self.refresh_vanilla_status()
                except OSError as exc:
                    messagebox.showerror("Vanilla baseline", str(exc))
                    return
        try:
            sell_pct = float(self.sell_pct_var.get()) / 100.0
        except ValueError:
            messagebox.showerror("Write", "Sell % must be a number.")
            return

        buy_path = shop / "buy_list.txt"
        sell_path = shop / "sell_list.txt"
        buy_existing, buy_header = parse_shop_list(buy_path)
        sell_existing, sell_header = parse_shop_list(sell_path)
        prefix = self.detected_module or self.module_var.get().strip() or "Base"

        buy_merged, sell_merged, preview = preview_merge(
            buy_existing, sell_existing, self.scanned, prefix=prefix, sell_ratio=sell_pct
        )
        if not self._ask_preview(format_preview_text(preview, str(shop))):
            return

        if not buy_header:
            buy_header = [
                "# IKappaID Phone Shop — buy list",
                f"# Merged from {prefix} via Shop List Editor",
            ]
        if not sell_header:
            sell_header = [
                "# IKappaID Phone Shop — sell list",
                f"# ~{int(sell_pct * 100)}% of buy for {prefix}",
            ]

        write_shop_list(buy_path, buy_merged, buy_header, backup=True)
        write_shop_list(sell_path, sell_merged, sell_header, backup=True)

        sync_msg = ""
        if self.sync_var.get():
            synced = sync_phoneshop_lists(shop, BUNDLE_ROOT)
            if synced:
                sync_msg = "\n\nSynced to:\n" + "\n".join(f"  • {d}" for d, _ in synced)
            else:
                sync_msg = "\n\n(No other Phone Shop folders to sync.)"

        self._persist_config()
        self.status_var.set(f"Wrote buy={preview.buy_after} sell={preview.sell_after} fp={preview.fp_after}")
        messagebox.showinfo(
            "Done",
            f"Updated:\n{buy_path}\n{sell_path}\n\nfp={preview.fp_after}{sync_msg}\n\n"
            "Restart the game or server to load new lists.",
        )

    def save_vanilla(self) -> None:
        shop = Path(self.shop_var.get().strip())
        if not shop.is_dir():
            messagebox.showerror("Vanilla baseline", "Phone Shop folder not set.")
            return
        if has_vanilla_baseline(shop):
            if not messagebox.askyesno(
                "Replace vanilla baseline?",
                "A baseline already exists. Overwrite it with the current lists?",
            ):
                return
        try:
            dest = save_vanilla_baseline(shop, note="manual save from editor")
        except OSError as exc:
            messagebox.showerror("Vanilla baseline", str(exc))
            return
        self.refresh_vanilla_status()
        self.status_var.set(f"Vanilla baseline saved → {dest}")
        messagebox.showinfo(
            "Vanilla baseline saved",
            f"Stored a copy of your current lists under:\n{dest}\n\n"
            "Use “Restore vanilla” anytime lists go wrong.",
        )

    def restore_vanilla(self) -> None:
        shop = Path(self.shop_var.get().strip())
        if not shop.is_dir():
            messagebox.showerror("Restore vanilla", "Phone Shop folder not set.")
            return
        if not has_vanilla_baseline(shop):
            messagebox.showwarning(
                "Restore vanilla",
                "No baseline saved yet.\n\nUse “Save vanilla baseline” while your lists are still good.",
            )
            return
        if not messagebox.askyesno(
            "Restore vanilla baseline?",
            "Replace current buy/sell (and other list files) with the saved vanilla baseline?\n\n"
            "Current files get a .pre_restore backup.",
        ):
            return
        try:
            restored = restore_vanilla_baseline(shop, backup_current=True)
        except OSError as exc:
            messagebox.showerror("Restore vanilla", str(exc))
            return
        sync_msg = ""
        if self.sync_var.get():
            synced = sync_phoneshop_lists(shop, BUNDLE_ROOT)
            if synced:
                sync_msg = f"\n\nSynced to {len(synced)} other folder(s)."
        self.refresh_vanilla_status()
        self.status_var.set(f"Restored vanilla baseline ({len(restored)} files)")
        messagebox.showinfo("Restored", f"Vanilla lists restored:{sync_msg}")

    def undo_write(self) -> None:
        shop = Path(self.shop_var.get().strip())
        if not shop.is_dir():
            messagebox.showerror("Undo", "Phone Shop folder not set.")
            return
        buy = shop / "buy_list.txt"
        sell = shop / "sell_list.txt"
        rb = restore_from_backup(buy)
        rs = restore_from_backup(sell)
        if not rb and not rs:
            messagebox.showinfo("Undo", "No backup files found (.bak.timestamp).")
            return
        self.status_var.set(f"Restored from backup — buy: {rb.name if rb else '—'}, sell: {rs.name if rs else '—'}")
        messagebox.showinfo("Undo", "Restored latest backups.\nSync other folders manually if needed.")


def main() -> None:
    app = ShopListEditorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
