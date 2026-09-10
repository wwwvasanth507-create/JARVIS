"""
JARVIS Desktop UI Theme & Design System.

Defines color palette, typography, padding constants, and custom TTK styles
for a sleek, CPU-friendly dark obsidian desktop aesthetic.
"""

from typing import Dict, Any

# Color Palette (Obsidian Dark Aesthetic)
BG_DARK = "#0d1117"            # Main Window Background
BG_SURFACE = "#161b22"         # Card & Frame Container Background
BG_INPUT = "#21262d"           # Text Entry Background
BORDER_COLOR = "#30363d"       # Subtle Frame Borders

TEXT_PRIMARY = "#c9d1d9"       # Primary Body Text
TEXT_MUTED = "#8b949e"         # Muted Secondary Text / Timestamps
TEXT_BRIGHT = "#f0f6fc"        # Titles & Headers

CYAN_ACCENT = "#58a6ff"        # JARVIS Accent / Buttons / Links
GREEN_SUCCESS = "#238636"      # READY / ONLINE / Verification Pass
YELLOW_WARN = "#d29922"         # DEGRADED / Warning / Waiting Confirmation
RED_ERROR = "#f85149"          # FAILED / UNAVAILABLE / Error
PURPLE_VOICE = "#a371f7"       # Voice & Wake Word Active

FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_SUBTITLE = ("Segoe UI", 11, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_MUTED = ("Segoe UI", 9)
FONT_MONO = ("Consolas", 9)

PAD_S = 4
PAD_M = 8
PAD_L = 16


def apply_ttk_theme(root) -> None:
    """Applies custom dark obsidian theme to TTK widget hierarchy."""
    import tkinter as tk
    from tkinter import ttk

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # Root background
    root.configure(bg=BG_DARK)

    # Base Frame & Label styles
    style.configure(".", background=BG_DARK, foreground=TEXT_PRIMARY, font=FONT_BODY)
    style.configure("TFrame", background=BG_DARK)
    style.configure("Surface.TFrame", background=BG_SURFACE, relief="flat", borderwidth=1)
    
    style.configure("TLabel", background=BG_DARK, foreground=TEXT_PRIMARY, font=FONT_BODY)
    style.configure("Surface.TLabel", background=BG_SURFACE, foreground=TEXT_PRIMARY, font=FONT_BODY)
    style.configure("Title.TLabel", background=BG_DARK, foreground=TEXT_BRIGHT, font=FONT_TITLE)
    style.configure("Muted.TLabel", background=BG_DARK, foreground=TEXT_MUTED, font=FONT_MUTED)
    style.configure("HeaderStatus.TLabel", background=BG_SURFACE, foreground=GREEN_SUCCESS, font=FONT_SUBTITLE)

    # Button styles
    style.configure(
        "TButton",
        background=BG_INPUT,
        foreground=TEXT_PRIMARY,
        bordercolor=BORDER_COLOR,
        focuscolor=CYAN_ACCENT,
        padding=(PAD_M, PAD_S),
        font=FONT_BODY
    )
    style.map(
        "TButton",
        background=[("active", BORDER_COLOR), ("disabled", BG_DARK)],
        foreground=[("active", TEXT_BRIGHT), ("disabled", TEXT_MUTED)]
    )

    style.configure(
        "Accent.TButton",
        background=CYAN_ACCENT,
        foreground="#000000",
        font=("Segoe UI", 10, "bold"),
        padding=(PAD_M, PAD_S)
    )
    style.map(
        "Accent.TButton",
        background=[("active", "#79c0ff")]
    )

    style.configure(
        "Stop.TButton",
        background=RED_ERROR,
        foreground="#ffffff",
        font=("Segoe UI", 10, "bold"),
        padding=(PAD_M, PAD_S)
    )

    # Entry fields
    style.configure("TEntry", fieldbackground=BG_INPUT, foreground=TEXT_PRIMARY, bordercolor=BORDER_COLOR)

    # Scrollbar
    style.configure("TScrollbar", background=BG_INPUT, bordercolor=BORDER_COLOR, arrowcolor=TEXT_MUTED)

    # Notebook Tabs
    style.configure("TNotebook", background=BG_DARK, borderwidth=0)
    style.configure("TNotebook.Tab", background=BG_SURFACE, foreground=TEXT_MUTED, padding=(PAD_M, PAD_S))
    style.map("TNotebook.Tab", background=[("selected", BG_INPUT)], foreground=[("selected", CYAN_ACCENT)])
