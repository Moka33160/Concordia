"""
File: palette.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: The colors, the fonts and the card sizes shared by the views.
"""

# --- Colours ---
# Three grounds, darkest first.
BACKGROUND = "#241d17"
PANEL_BACKGROUND = "#33291f"
STATUS_BACKGROUND = "#1a140f"

# The hairline around a panel, and the ground of a raised panel.
PANEL_EDGE = "#4a3c2d"
PANEL_RAISED = "#413425"

MAP_BACKGROUND = "#f2e9d6"

TEXT_COLOR = "#ede4cf"
MUTED_COLOR = "#a8977c"

# Three golds of the same family, told apart by lightness and not by hue.

# What the action offers. The brightest colour, and always clickable.
HIGHLIGHT = "#f0c247"
HIGHLIGHT_WIDTH = 4

# Headings, the current player and the main button.
ACCENT = "#d9a83c"
ACCENT_INK = "#241d17"

# The capital is drawn on parchment, so the darkest gold of the family.
CAPITAL_COLOR = "#b07d24"

# --- Cards ---
CARD_FACE = "#f4ecd8"
CARD_BORDER = "#3a2f24"
CARD_BANNER = "#5a4632"
CARD_INK = "#2e2419"
CARD_SHADOW = "#160f0a"

# A selected card is rimmed in parchment: gold means offered by the action.
CARD_SELECTED = "#e8dcc0"

# --- Map ---

# The ink of everything on the parchment: city rims, labels, marker edges.
MAP_INK = "#3a2f24"

# The casing under every route, so a crossing has an over and an under.
ROUTE_CASING = "#e0d3b8"

# The gold used on the parchment, dark enough to be read on cream.
MAP_ACCENT = "#8f6413"

# The ground of each province, saying which cities share a bonus marker.
PROVINCE_TINTS = (
    "#7d9b63",  # sage
    "#c1845c",  # terracotta
    "#7d97b8",  # dusty blue
    "#9b7fa6",  # mauve
    "#b0a052",  # olive
    "#5f9691",  # teal
    "#c07f83",  # rose
    "#7379ad",  # indigo
)

# How much tint the ground keeps, and how much more the line around it.
PROVINCE_WASH = 0.28
PROVINCE_EDGE = 0.52

# A canvas item has no alpha, and a stipple is drawn solid on macOS.

# How far towards its background a thing is blended to push it back.
MAP_MUTE = 0.78
CARD_MUTE = 0.55

# Lettering recedes far less than the graphics it sits on.
LABEL_MUTE = 0.45

# The swatch of a good of the player's choice, not the colour of a real good.
ANY_GOOD_FILL = "#cfc7b4"

# --- Type ---
# Two faces.
SERIF_FACES = (
    "Palatino", "Palatino Linotype", "Book Antiqua", "Georgia",
    "Times New Roman", "serif",
)
SANS_FACES = (
    "Avenir Next", "Segoe UI", "Helvetica Neue", "DejaVu Sans", "Arial",
    "sans-serif",
)

# Kept for callers that name a family rather than ask for a font.
FONT = SERIF_FACES[0]

# The scale.
SIZE_MICRO = 9
SIZE_SMALL = 10
SIZE_BODY = 12
SIZE_LEAD = 14
SIZE_TITLE = 20

# The unit every gap and padding is a multiple of.
SPACE_1 = 4
SPACE_2 = 8
SPACE_3 = 12
SPACE_4 = 16
SPACE_5 = 24
SPACE_6 = 32

_FACES: dict[tuple[str, ...], str] = {}


def _resolve(preferred: tuple[str, ...]) -> str:
    """The first of a run of family names that Tk actually has."""
    if preferred in _FACES:
        return _FACES[preferred]

    found = preferred[0]
    try:
        import tkinter.font as tk_font

        available = set(tk_font.families())
        found = next(
            (name for name in preferred if name in available), preferred[0]
        )
    except (ImportError, RuntimeError):
        # No Tk yet: the first name is a family every desktop has.
        return found

    _FACES[preferred] = found
    return found


def serif(size: int, *styles: str) -> tuple:
    """A font tuple in the game's serif, for names, headings and the market."""
    return _font(_resolve(SERIF_FACES), size, styles)


def sans(size: int, *styles: str) -> tuple:
    """
    A font tuple in the interface's sans, for counts, prompts and buttons.
    """
    return _font(_resolve(SANS_FACES), size, styles)


def _font(family: str, size: int, styles: tuple[str, ...]) -> tuple:
    """Build the font tuple, leaving the style off when there is none."""
    return (family, size, " ".join(styles)) if styles else (family, size)


# --- Card metrics ---
# The base a `Layout` scales from.
CARD_WIDTH = 88
CARD_HEIGHT = 134
CARD_NAME_BAND = 30
CARD_GOD_BAND = 20
HOVER_SCALE = 1.25

# How much of a resting card shows above the bottom of the window.
HAND_PEEK = 52

# --- Table metrics ---
# The floor a `Layout` starts from, and what it falls back to.
TABLE_WIDTH = 1160
# Deep enough for a card plus the row of goods it is bought with.
MARKET_BAND = 138
MAP_BAND = 520
# The gap between the foot of the board and the hand resting under it.
HAND_GUTTER = 18
TABLE_HEIGHT = MARKET_BAND + MAP_BAND + HAND_GUTTER + HAND_PEEK


# --- Blending ---

def _channels(color: str) -> tuple[int, int, int] | None:
    """The three channels of a "#rrggbb" colour."""
    value = color.lstrip("#")

    if len(value) != 6:
        return None

    try:
        return tuple(int(value[n:n + 2], 16) for n in (0, 2, 4))
    except ValueError:
        return None


def blend(color: str, toward: str, amount: float) -> str:
    """
    Move a colour part of the way towards another.

    :param color: The colour to move.
    :param toward: The colour to move it towards.
    :param amount: How far, 0 leaving it alone and 1 replacing it.
    :return: The blended colour as "#rrggbb", or `color` when either side is a
        named colour.
    """
    start = _channels(color)
    end = _channels(toward)

    if start is None or end is None:
        return color

    amount = min(max(amount, 0.0), 1.0)
    mixed = (
        round(left + (right - left) * amount)
        for left, right in zip(start, end)
    )
    return "#{:02x}{:02x}{:02x}".format(*mixed)


def ink_on(color: str) -> str:
    """The lettering colour that reads on a given ground."""
    channels = _channels(color)

    if channels is None:
        return CARD_INK

    red, green, blue = channels
    luminance = (0.299 * red + 0.587 * green + 0.114 * blue) / 255

    return CARD_INK if luminance > 0.5 else CARD_FACE


def muted(color: str, on: bool = True) -> str:
    """
    A map colour pushed back towards the parchment, or left alone.

    :param color: The colour as it is drawn when nothing is highlighted.
    :param on: Whether to push it back at all.
    :return: The colour to draw with.
    """
    return blend(color, MAP_BACKGROUND, MAP_MUTE) if on else color


def lettered(color: str, on: bool = True) -> str:
    """
    A map colour pushed back only as far as lettering may go.

    :param color: The colour the label is drawn in when nothing is
        highlighted.
    :param on: Whether to push it back at all.
    :return: The colour to draw with.
    """
    return blend(color, MAP_BACKGROUND, LABEL_MUTE) if on else color
