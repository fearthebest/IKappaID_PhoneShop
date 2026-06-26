"""Phone Shop UI palette — matches in-game shop (dark + orange)."""

BG = "#1a1a1a"
CARD = "#2b2b2b"
CHIP = "#3d3d3d"
ORANGE = "#ff6600"
ORANGE_HOVER = "#cc5200"
ORANGE_DIM = "#bf5c00"
TEXT = "#f2f2f2"
MUTED = "#9a9a9a"
BORDER = "#404040"
SELECT = "#4a2a10"
DANGER = "#e84d40"
OK = "#73d985"

ACCENT_THEME = {
    "CTk": {"fg_color": BG},
    "CTkFrame": {"fg_color": CARD, "border_color": BORDER},
    "CTkLabel": {"text_color": TEXT},
    "CTkEntry": {
        "fg_color": CHIP,
        "border_color": BORDER,
        "text_color": TEXT,
        "placeholder_text_color": MUTED,
    },
    "CTkButton": {
        "fg_color": ORANGE,
        "hover_color": ORANGE_HOVER,
        "text_color": TEXT,
        "border_color": ORANGE_DIM,
    },
    "CTkCheckBox": {
        "fg_color": ORANGE,
        "hover_color": ORANGE_HOVER,
        "border_color": BORDER,
        "text_color": TEXT,
    },
    "CTkToplevel": {"fg_color": BG},
    "CTkTextbox": {
        "fg_color": CHIP,
        "border_color": BORDER,
        "text_color": TEXT,
    },
}
